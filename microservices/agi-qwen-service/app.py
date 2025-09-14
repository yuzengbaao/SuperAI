from flask import Flask, jsonify, request
import redis
import json
import os
import requests
from datetime import datetime
import sys
import threading

# Add the core directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'core')))
from core.event_bus import EventBus

app = Flask(__name__)

# --- Initialize Core Components ---
# Initialize the distributed Event Bus
try:
    event_bus = EventBus()
    print("✅ [agi-qwen-service] Event Bus initialized successfully.")
except Exception as e:
    print(f"❌ [agi-qwen-service] CRITICAL: Failed to initialize Event Bus. Error: {e}")
    event_bus = None

listener_thread = None # Will hold the background listener thread

# Connect to Redis for direct data operations if needed
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'agi-redis-lb'), port=6379, db=0, decode_responses=True)

# --- Start Background Tasks ---
def start_background_tasks():
    """Initialize and start background tasks like event listeners."""
    global listener_thread
    if event_bus and not listener_thread:
        print("🚀 [agi-qwen-service] Starting event listener thread...")
        listener_thread = threading.Thread(target=start_event_listener, daemon=True)
        listener_thread.start()
        print("✅ [agi-qwen-service] Event listener thread started successfully.")

# Get vLLM API configuration from environment variables
VLLM_API_URL = os.getenv('VLLM_API_URL')
VLLM_MODEL = os.getenv('VLLM_MODEL')

# --- Event Listeners ---

def handle_user_question(event_type, data):
    """
    Listener for 'user_question_received' event.
    Processes the user's question, calls the LLM, and publishes the response.
    """
    print(f"🧠 [agi-qwen-service] Received event '{event_type}' with data: {data}")
    
    # Get prompt from either 'prompt' or 'text' key for better compatibility
    prompt = data.get('prompt') or data.get('text')
    if not prompt:
        print("⚠️ [agi-qwen-service] Event data is missing 'prompt' or 'text'.")
        return

    if not VLLM_API_URL:
        print("❌ [agi-qwen-service] VLLM_API_URL is not set. Cannot process the request.")
        event_bus.publish('llm_api_error', data={"error": "VLLM_API_URL not configured", "prompt": prompt})
        return

    headers = {'Content-Type': 'application/json'}
    payload = {
        "model": VLLM_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(VLLM_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        vllm_response = response.json()
        generated_text = vllm_response.get('choices', [{}])[0].get('message', {}).get('content', 'No text generated.')
        
        # Publish the result back to the event bus
        response_event_data = {
            "original_prompt": prompt,
            "generated_text": generated_text,
            "model": VLLM_MODEL,
            "source_service": "agi-qwen-service"
        }
        event_bus.publish('llm_response_generated', data=response_event_data)
        print(f"✅ [agi-qwen-service] Successfully processed prompt and published 'llm_response_generated'.")

    except requests.exceptions.RequestException as e:
        print(f"❌ [agi-qwen-service] Error calling vLLM API: {e}")
        # Optionally, publish an error event
        error_data = {"error": str(e), "prompt": prompt}
        event_bus.publish('llm_api_error', data=error_data)

def start_event_listener():
    """
    Subscribes to relevant events and starts the blocking listener.
    This function is intended to be run in a background thread.
    """
    # --- Subscribe to Events ---
    event_bus.subscribe('user_question_received', handle_user_question)
    event_bus.subscribe('*', lambda event_type, data: print(f"📢 [agi-qwen-service] Wildcard: Saw event '{event_type}'"))
    print("👂 [agi-qwen-service] Subscribed to 'user_question_received'. Starting event listener...")
    # This is a blocking call
    event_bus.listen()

# Start background tasks when module is loaded (after function definitions)
start_background_tasks()

# --- RESTful API Endpoints (for direct interaction and health checks) ---

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify service status and Redis connection.
    """
    try:
        redis_client.ping()
        redis_status = "healthy"
    except redis.ConnectionError:
        redis_status = "unhealthy"
    
    vllm_config_status = "set" if VLLM_API_URL and VLLM_MODEL else "not_set"
    
    return jsonify({
        "status": "healthy", 
        "redis": redis_status,
        "vllm_config": vllm_config_status,
        "event_bus_listener_alive": listener_thread.is_alive() if listener_thread else False
    }), 200

@app.route('/generate', methods=['POST'])
def generate_text():
    """
    Generates text by calling the vLLM OpenAI-compatible API and logs the interaction to Redis.
    This endpoint can be used for direct testing.
    """
    input_data = request.get_json()
    if not input_data or 'prompt' not in input_data:
        return jsonify({"error": "Invalid input. 'prompt' is required."}), 400
    
    prompt = input_data.get('prompt')
    
    # Instead of handling the logic here, we publish an event
    # This demonstrates how the API gateway would interact with the system
    event_data = {
        "prompt": prompt,
        "request_id": f"req_{datetime.utcnow().isoformat()}"
    }
    event_bus.publish('user_question_received', data=event_data)
    
    return jsonify({"status": "success", "message": "Event 'user_question_received' published."}), 202


if __name__ == '__main__':
    if not event_bus:
        print("❌ [agi-qwen-service] Cannot start due to Event Bus initialization failure. Exiting.")
        sys.exit(1)

    print("🚀 [agi-qwen-service] Starting Flask application...")
    app.run(host='0.0.0.0', port=int(os.getenv("SERVICE_PORT", 8200)), debug=False)



