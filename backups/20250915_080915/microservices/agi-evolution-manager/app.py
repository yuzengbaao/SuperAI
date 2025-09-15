from flask import Flask, jsonify
import redis
import os
from core.event_bus import EventBus
import threading

app = Flask(__name__)

# --- Initialize Core Components ---
# 全局事件总线实例
event_bus = EventBus()

# Connect to Redis for direct data operations
# Use a different database (e.g., db=1) for memories to keep them separate
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'agi-redis-lb'), port=6379, db=1, decode_responses=True)
print(f"💾 [Memory] Evolution Manager connected to Redis DB 1 for memory storage.")

# --- Event Listeners ---

def store_memory(event_type, data):
    """
    Listener for 'llm_response_generated' event.
    Stores the question and answer pair in Redis as a long-term memory.
    """
    print(f"🧠 [Memory] Received event '{event_type}' to store a new memory.")
    
    question = data.get('original_prompt')
    answer = data.get('generated_text')

    if not question or not answer:
        print("⚠️ [Memory] Event data is missing 'original_prompt' or 'generated_text'.")
        return

    try:
        # Using a simple HASH to store memories. Key: "memory:knowledge_base"
        # Field: question, Value: answer
        redis_client.hset("memory:knowledge_base", question, answer)
        print(f"✅ [Memory] Successfully stored memory: '{question[:50]}...'")

    except redis.RedisError as e:
        print(f"❌ [Memory] Failed to store memory in Redis: {e}")

# --- Subscribe to Events ---
event_bus.subscribe('llm_response_generated', store_memory)
print("👂 [Memory] Subscribed to 'llm_response_generated' to listen for new knowledge.")


# --- RESTful API Endpoints ---

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify service status and Redis connection.
    """
    try:
        redis_client.ping()
        redis_ok = True
    except redis.ConnectionError:
        redis_ok = False

    # 检查记忆Redis的连接
    try:
        memory_redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'agi-redis-lb'), port=6379, db=1, decode_responses=True)
        memory_redis_client.ping()
        memory_redis_ok = True
    except redis.ConnectionError:
        memory_redis_ok = False

    health_status = {
        "status": "healthy" if redis_ok and memory_redis_ok else "unhealthy",
        "redis_connection": "OK" if redis_ok else "Failed",
        "redis_memory_connection": "OK" if memory_redis_ok else "Failed",
    }
    
    status_code = 200 if redis_ok and memory_redis_ok else 503
    return jsonify(health_status), status_code

# 启动事件总线并开始监听
def start_event_listener():
    # 使用全局的event_bus实例
    event_bus.subscribe('llm_response_generated', store_memory)
    print(f"👂 [Memory] Subscribed to 'llm_response_generated' to listen for new knowledge.")
    # 启动阻塞式监听
    event_bus.listen()

if __name__ == '__main__':
    # 在后台线程中启动事件监听器
    listener_thread = threading.Thread(target=start_event_listener, daemon=True)
    listener_thread.start()
    
    # 运行Flask应用
    # 注意：在生产环境中，应使用Gunicorn或uWSGI等WSGI服务器
    app.run(host='0.0.0.0', port=8300, debug=False)
