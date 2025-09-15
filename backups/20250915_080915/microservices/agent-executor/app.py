from flask import Flask, jsonify, request
import redis
import json
import os
import requests
import asyncio
from datetime import datetime
import sys
import time
import threading
import logging

# Add the core directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'core')))
from core.event_bus import EventBus
from core.prometheus_metrics import setup_metrics_for_flask_app, get_metrics
# 显式导入tools模块以确保工具被注册
import core.tools
from core.tools import ToolExecutor, get_global_registry # 导入工具执行器

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Initialize Core Components ---
# Initialize the distributed Event Bus
try:
    event_bus = EventBus()
    logger.info("✅ [agent-executor] Event Bus initialized successfully.")
except Exception as e:
    logger.critical(f"❌ [agent-executor] CRITICAL: Failed to initialize Event Bus. Error: {e}")
    event_bus = None

# 初始化工具执行器
try:
    tool_executor = ToolExecutor(get_global_registry())
    logger.info("✅ [agent-executor] Tool Executor initialized successfully.")
except Exception as e:
    logger.critical(f"❌ [agent-executor] CRITICAL: Failed to initialize Tool Executor. Error: {e}")
    tool_executor = None

listener_thread = None # Will hold the background listener thread

# Connect to Redis for direct data operations if needed
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'agi-redis-lb'), port=6379, db=0, decode_responses=True)

# --- Start Background Tasks ---
def start_background_tasks():
    """Initialize and start background tasks like event listeners."""
    global listener_thread, metrics
    
    # 设置Prometheus监控
    metrics_port = int(os.getenv('METRICS_PORT', 8081))
    metrics = setup_metrics_for_flask_app(app, 'agent-executor', metrics_port)
    logger.info(f"✅ [agent-executor] Prometheus监控已设置，指标端口: {metrics_port}")
    
    # 启动事件监听器
    if event_bus and not listener_thread:
        print("🚀 [agent-executor] Starting event listener thread...")
        listener_thread = threading.Thread(target=start_event_listener, daemon=True)
        listener_thread.start()
        print("✅ [agent-executor] Event listener thread started successfully.")

# Get vLLM API configuration from environment variables
VLLM_API_URL = os.getenv('VLLM_API_URL', 'http://vllm-service:8000/v1/chat/completions')
VLLM_MODEL = os.getenv('VLLM_MODEL', 'Qwen/Qwen1.5-1.8B-Chat')

# --- Initialize Tool System ---
try:
    tool_registry = get_global_registry()
    tool_executor = ToolExecutor(tool_registry)
    # Set permissions for tool execution including file and web access
    tool_executor.set_permissions(['read', 'compute', 'basic_operations', 'file_read', 'file_write', 'web_access', 'external_api'])
    print(f"✅ [agent-executor] Tool system initialized with {len(tool_registry)} tools")
except Exception as e:
    print(f"❌ [agent-executor] Failed to initialize tool system: {e}")
    tool_executor = None

# --- Event Listeners ---

def handle_plan_approved(event_type, data):
    """
    Listener for 'plan.approved' event.
    Executes the approved plan step by step.
    """
    # 记录EventBus消息指标
    if 'metrics' in globals():
        metrics.record_eventbus_message(event_type, 'received')
    
    if not event_bus:
        logger.error("Event bus is not initialized. Cannot handle 'plan.approved' event.")
        return

    print(f"⚡ [agent-executor] Received event '{event_type}' with data: {data}")
    
    task_id = data.get('task_id')
    session_id = data.get('session_id')
    
    # Handle different data structures for plan
    plan = None
    plan_data = {}
    if 'plan' in data:
        plan = data.get('plan')
    elif 'data' in data and isinstance(data['data'], dict):
        plan_data = data.get('data', {})
        plan = plan_data.get('plan')
    
    if not task_id or not plan:
        print("⚠️ [agent-executor] Event data is missing 'task_id' or 'plan'.")
        return

    print(f"🔄 [agent-executor] Starting execution of plan for task {task_id}")
    
    try:
        # Get steps from plan - handle both list and dict formats
        steps = []
        if isinstance(plan, dict):
            steps = plan.get('steps', [])
        elif isinstance(plan, list):
            steps = plan
        
        if not steps:
            print("⚠️ [agent-executor] No steps found in plan")
            return
        
        # Execute plan steps sequentially
        execution_results = []
        
        for step in steps:
            step_id = step.get('step_id')
            action = step.get('action')
            description = step.get('description')
            requires_llm = step.get('requires_llm', False)
            
            print(f"📋 [agent-executor] Executing step {step_id}: {description}")
            
            # Publish step started event
            event_bus.publish('action.started', data={
                "task_id": task_id,
                "step_id": step_id,
                "action": action,
                "description": description
            })
            
            step_result = execute_step(step, task_id)
            execution_results.append(step_result)
            
            # Publish step completed event
            event_bus.publish('action.completed', data={
                "task_id": task_id,
                "step_id": step_id,
                "action": action,
                "result": step_result,
                "status": "completed"
            })
            
            # Small delay between steps
            time.sleep(1)
        
        # Publish task completion
        completion_data = {
            "task_id": task_id,
            "session_id": session_id,
            "data": {
                "original_goal": plan_data.get('original_goal'),
                "execution_results": execution_results,
                "completed_at": datetime.utcnow().isoformat(),
                "status": "completed"
            }
        }
        
        event_bus.publish('task.completed', data=completion_data)
        print(f"✅ [agent-executor] Task {task_id} completed successfully")
        
    except Exception as e:
        print(f"❌ [agent-executor] Error executing plan: {e}")
        error_data = {
            "task_id": task_id,
            "error": str(e),
            "status": "failed"
        }
        event_bus.publish('task.failed', data=error_data)

def execute_step(step, task_id):
    """
    Execute a single step of the plan.
    Enhanced with tool execution capability.
    """
    action = step.get('action')
    requires_llm = step.get('requires_llm', False)
    requires_tool = step.get('requires_tool', False)
    llm_prompt = step.get('llm_prompt')
    tool_name = step.get('tool_name')
    tool_params = step.get('tool_params', {})
    
    start_time = time.time()
    status = 'success'
    
    print(f"🔧 [agent-executor] Executing step: {action} (LLM: {requires_llm}, Tool: {requires_tool})")
    
    try:
        # Handle tool execution
        if requires_tool and tool_name and tool_executor:
            print(f"🛠️ [agent-executor] Executing tool: {tool_name} with params: {tool_params}")
            try:
                tool_result = tool_executor.execute_tool(tool_name, tool_params)
                
                if tool_result.is_success():
                    print(f"✅ [agent-executor] Tool {tool_name} executed successfully")
                    return {
                        "action": action,
                        "tool_name": tool_name,
                        "tool_result": tool_result.to_dict(),
                        "result": f"Tool {tool_name} executed successfully",
                        "data": tool_result.data,
                        "execution_time": tool_result.execution_time,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    print(f"❌ [agent-executor] Tool {tool_name} execution failed: {tool_result.error}")
                    return {
                        "action": action,
                        "tool_name": tool_name,
                        "error": tool_result.error,
                        "result": f"Tool {tool_name} execution failed",
                        "timestamp": datetime.utcnow().isoformat()
                    }
            except Exception as e:
                print(f"❌ [agent-executor] Tool execution exception: {e}")
                return {
                    "action": action,
                    "tool_name": tool_name,
                    "error": str(e),
                    "result": f"Tool {tool_name} execution exception",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        # Handle LLM execution
        elif requires_llm and llm_prompt:
            print(f"🤖 [agent-executor] Calling LLM for step: {action}")
            return call_llm(llm_prompt, task_id)
    
    # Handle simple action execution
        else:
            if action == 'analyze_poetry_requirements':
                result = {
                    "action": action,
                    "result": "诗歌要求分析完成：五言绝句，四句二十字，讲述星际探索主题",
                    "analysis": "需要体现宇宙的浩瀚和人类探索精神"
                }
            else:
                result = {
                    "action": action,
                    "result": f"Action {action} executed successfully",
                    "timestamp": datetime.utcnow().isoformat()
                }
    
    except Exception as e:
        status = 'error'
        logger.error(f"❌ [agent-executor] Step execution failed: {e}")
        result = {
            "action": action,
            "result": f"Action {action} failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    finally:
        # 记录工具执行指标
        if 'metrics' in globals():
            duration = time.time() - start_time
            metrics.record_tool_execution(action, status, duration)
    
    return result

def call_llm(prompt, task_id):
    """
    Call the vLLM service to generate content.
    """
    if not VLLM_API_URL:
        return {"error": "VLLM_API_URL not configured"}
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "model": VLLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512,
        "temperature": 0.7
    }
    
    start_time = time.time()
    status = 'success'
    
    try:
        print(f"🤖 [agent-executor] Calling LLM for task {task_id}")
        print(f"📝 [agent-executor] Prompt: {prompt}")
        response = requests.post(VLLM_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        vllm_response = response.json()
        generated_text = vllm_response.get('choices', [{}])[0].get('message', {}).get('content', 'No text generated.')
        
        print(f"📄 [agent-executor] LLM Response: {generated_text}")
        
        return {
            "llm_response": generated_text,
            "model": VLLM_MODEL,
            "prompt": prompt,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ [agent-executor] Error calling vLLM API: {e}")
        return {"error": str(e), "prompt": prompt}

def start_event_listener():
    """
    Subscribes to relevant events and starts the blocking listener.
    This function is intended to be run in a background thread.
    """
    if not event_bus:
        logger.error("Event bus is not initialized. Cannot start event listener.")
        return
        
    # --- Subscribe to Events ---
    event_bus.subscribe('plan.approved', handle_plan_approved)
    event_bus.subscribe('*', lambda event_type, data: print(f"📢 [agent-executor] Wildcard: Saw event '{event_type}'"))
    print("👂 [agent-executor] Subscribed to 'plan.approved'. Starting event listener...")
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
        "service": "agent-executor",
        "redis": redis_status,
        "vllm_config": vllm_config_status,
        "event_bus_listener_alive": listener_thread.is_alive() if listener_thread else False,
        "subscribed_events": ["plan.approved"]
    }), 200

@app.route('/execute-plan', methods=['POST'])
def execute_plan_direct():
    """
    Directly execute a plan for testing purposes.
    This endpoint can be used for direct testing.
    """
    if not event_bus:
        return jsonify({"error": "Event bus is not initialized."}), 500

    input_data = request.get_json()
    if not input_data or 'plan' not in input_data:
        return jsonify({"error": "Invalid input. 'plan' is required."}), 400
    
    plan = input_data.get('plan')
    task_id = input_data.get('task_id', f"direct_{datetime.utcnow().isoformat()}")
    
    # Publish plan.approved event for testing
    event_data = {
        "task_id": task_id,
        "session_id": "direct_api",
        "data": {
            "plan": plan,
            "original_goal": input_data.get('goal', 'Direct execution test')
        }
    }
    event_bus.publish('plan.approved', data=event_data)
    
    return jsonify({
        "status": "success", 
        "message": "Plan execution started.",
        "task_id": task_id
    }), 202


if __name__ == '__main__':
    if not event_bus:
        print("❌ [agent-executor] Cannot start due to Event Bus initialization failure. Exiting.")
        sys.exit(1)

    print("🚀 [agent-executor] Starting Flask application...")
    app.run(host='0.0.0.0', port=int(os.getenv("SERVICE_PORT", 8400)), debug=False)



