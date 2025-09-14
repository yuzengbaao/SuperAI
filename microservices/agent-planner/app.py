import os
import sys
import logging
from datetime import datetime
import re

# Apply gevent monkey patching BEFORE importing redis
import gevent.monkey
gevent.monkey.patch_all(thread=False, select=False)

import redis
import gevent

# Add the core directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'core')))
from core.event_bus import EventBus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("agent-planner")


# This is a placeholder for the Flask app if you add REST endpoints
# For now, it's not used by gunicorn but is needed for the import structure.
from flask import Flask, jsonify
app = Flask(__name__)

# --- Redis Connection ---
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'agi-redis-lb'), port=6379, db=0, decode_responses=True)

# --- Health Check Endpoint ---
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        redis_client.ping()
        redis_status = "healthy"
    except redis.ConnectionError:
        redis_status = "unhealthy"
    
    # Check if the listener greenlet is alive
    listener_alive = False
    if listener_greenlet is not None:
        listener_alive = not listener_greenlet.dead
    
    return jsonify({
        "status": "healthy",
        "service": "agent-planner",
        "redis": redis_status,
        "event_bus_listener_alive": listener_alive
    }), 200

# --- Helper Functions for Plan Creation ---

def extract_search_query(goal: str) -> str:
    """从目标中提取搜索查询"""
    patterns = [
        r"(?:搜索|查找|search for|find)\s*[:：]?\s*(.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, goal, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    if any(keyword in goal.lower() for keyword in ["搜索", "查找", "search", "find"]):
        return goal
    return goal

def extract_file_path(goal: str) -> str:
    """从目标中提取文件路径"""
    patterns = [
        r"读取文件[：:]?\s*([^\s]+)",
        r"读取\s+([^\s]+\.\w+)",
        r"查看文件[：:]?\s*([^\s]+)",
        r"文件[：:]?\s*([^\s]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, goal)
        if match:
            return match.group(1)
    return "/tmp/example.txt"

def extract_file_write_info(goal: str) -> dict:
    """从目标中提取文件写入信息"""
    path_patterns = [
        r"写入文件[：:]?\s*([^\s]+)",
        r"创建文件[：:]?\s*([^\s]+)",
        r"生成文件[：:]?\s*([^\s]+)"
    ]
    file_path = "/tmp/generated_file.txt"
    for pattern in path_patterns:
        match = re.search(pattern, goal)
        if match:
            file_path = match.group(1)
            break
    return {"path": file_path, "description": goal}

def extract_directory_path(goal: str) -> str:
    """从目标中提取目录路径"""
    patterns = [
        r"列出文件[：:]?\s*([^\s]+)",
        r"查看目录[：:]?\s*([^\s]+)",
        r"目录[：:]?\s*([^\s]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, goal)
        if match:
            return match.group(1)
    return "/tmp"

def extract_echo_message(goal: str) -> str:
    """从目标中提取回声消息"""
    patterns = [
        r"回声[：:]?\s*(.+)",
        r"echo[：:]?\s*(.+)",
        r"重复[：:]?\s*(.+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, goal, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return goal

def create_execution_plan(task_id: str, goal: str):
    """
    根据任务目标创建执行计划。
    """
    plan = {
        "task_id": task_id,
        "goal": goal,
        "steps": []
    }

    # Math task
    math_pattern = r"(计算|calculate)\s*([\d\.]+)\s*([+\-*/])\s*([\d\.]+)"
    math_match = re.search(math_pattern, goal, re.IGNORECASE)
    if math_match:
        _, num1, op, num2 = math_match.groups()
        op_map = {'+': 'add', '-': 'subtract', '*': 'multiply', '/': 'divide'}
        plan["steps"].append({
            "step_id": 1,
            "description": f"使用数学工具执行计算: {num1} {op} {num2}",
            "requires_tool": True,
            "tool_name": "math",
            "tool_params": {"operation": op_map.get(op), "a": float(num1), "b": float(num2)},
            "dependencies": []
        })
        return plan

    # Web search task
    if "搜索" in goal or "查找" in goal or "search" in goal.lower() or "find" in goal.lower():
        query = extract_search_query(goal)
        plan["steps"] = [
            {"step_id": 1, "description": f"执行网络搜索: {query}", "requires_tool": True, "tool_name": "web_search", "tool_params": {"operation": "search", "query": query}, "dependencies": []},
            {"step_id": 2, "description": "根据搜索结果进行分析和总结", "requires_llm": True, "tool_name": None, "tool_params": {}, "dependencies": [1]}
        ]
        return plan

    # File reading task
    if "读取文件" in goal or ("读取" in goal and "文件" in goal) or "查看文件" in goal:
        file_path = extract_file_path(goal)
        plan["steps"] = [
            {"step_id": 1, "description": f"读取文件：{file_path}", "requires_tool": True, "tool_name": "file_operations", "tool_params": {"operation": "read_file", "path": file_path, "encoding": "utf-8"}, "dependencies": []},
            {"step_id": 2, "description": "分析文件内容并生成总结", "requires_llm": True, "tool_name": None, "tool_params": {}, "dependencies": [1]}
        ]
        return plan

    # File writing task
    if "写入文件" in goal or "创建文件" in goal or "生成文件" in goal:
        file_info = extract_file_write_info(goal)
        plan["steps"] = [
            {"step_id": 1, "description": f"生成文件内容：{file_info['description']}", "requires_llm": True, "tool_name": None, "tool_params": {}, "dependencies": []},
            {"step_id": 2, "description": f"写入文件：{file_info['path']}", "requires_tool": True, "tool_name": "file_operations", "tool_params": {"operation": "write_file", "path": file_info['path'], "create_dirs": True}, "dependencies": [1]}
        ]
        return plan

    # Directory listing task
    if "列出文件" in goal or "查看目录" in goal or "目录内容" in goal:
        dir_path = extract_directory_path(goal)
        plan["steps"] = [
            {"step_id": 1, "description": f"列出目录内容：{dir_path}", "requires_tool": True, "tool_name": "file_operations", "tool_params": {"operation": "list_directory", "path": dir_path, "file_details": True}, "dependencies": []},
            {"step_id": 2, "description": "格式化目录列表", "requires_llm": True, "tool_name": None, "tool_params": {}, "dependencies": [1]}
        ]
        return plan

    # Echo task
    if "回声" in goal or "echo" in goal.lower() or "重复" in goal:
        message = extract_echo_message(goal)
        plan["steps"] = [
            {"step_id": 1, "description": f"使用回声工具处理消息：{message}", "requires_tool": True, "tool_name": "echo", "tool_params": {"message": message}, "dependencies": []},
            {"step_id": 2, "description": "格式化回声结果", "requires_llm": True, "tool_name": None, "tool_params": {}, "dependencies": [1]}
        ]
        return plan

    # Default plan
    plan["steps"] = [
        {"step_id": 1, "description": "分析任务需求和主题", "requires_llm": True, "tool_name": None, "tool_params": {}, "dependencies": []},
        {"step_id": 2, "description": "执行主要任务：调用LLM生成内容", "requires_llm": True, "tool_name": None, "tool_params": {}, "dependencies": [1]},
        {"step_id": 3, "description": "优化和格式化生成的内容", "requires_llm": True, "tool_name": None, "tool_params": {}, "dependencies": [2]}
    ]
    return plan


class PlannerAgent:
    def __init__(self):
        self.event_bus = EventBus()
        self.register_event_handlers()

    def register_event_handlers(self):
        self.event_bus.subscribe('task.created', self.handle_task_created)
        self.event_bus.subscribe('*', self.log_event)
        logger.info("✅ Event handlers registered.")

    def handle_task_created(self, event_type, data, max_retries=3):
        """处理新创建的任务，为其生成执行计划。使用Redis锁确保只有一个worker处理。"""
        task_id = data.get('task_id')
        if not task_id:
            logger.warning("⚠️ Event data is missing 'task_id'.")
            return

        # 重试机制
        for attempt in range(max_retries):
            try:
                return self._process_task_with_lock(task_id, data, attempt)
            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1} failed for task {task_id}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"💥 All {max_retries} attempts failed for task {task_id}")
                    self._publish_error_event(task_id, str(e), data.get('data', {}).get('goal', 'Unknown'))
                else:
                    # 指数退避
                    wait_time = 2 ** attempt
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    gevent.sleep(wait_time)

    def _process_task_with_lock(self, task_id, data, attempt):
        """使用分布式锁处理任务的核心逻辑"""
        # 使用Redis实现分布式锁，确保只有一个worker处理此任务
        lock_key = f"lock:task_created:{task_id}"
        
        # 尝试获取锁，如果键已存在（被其他worker获取），setnx返回0
        try:
            if not redis_client.set(lock_key, f"locked_attempt_{attempt}", nx=True, ex=60): # 60秒后自动过期
                logger.info(f"🔄 Task {task_id} is already being processed by another worker. Skipping.")
                return
        except Exception as e:
            logger.error(f"❌ Failed to acquire lock for task {task_id}: {e}")
            raise

        logger.info(f"🎯 Acquired lock for task {task_id} (attempt {attempt + 1}). Processing...")
        
        session_id = data.get('session_id')
        goal = data.get('data', {}).get('goal')
        
        if not goal:
            logger.warning("⚠️ Event data is missing 'goal'.")
            self._safe_release_lock(lock_key, task_id)
            return

        logger.info(f"📋 Creating plan for task {task_id}: {goal}")
        
        try:
            plan = create_execution_plan(task_id, goal)
            
            plan_data = {
                "task_id": task_id,
                "session_id": session_id,
                "data": {
                    "original_goal": goal,
                    "plan": plan,
                    "estimated_steps": len(plan.get("steps", [])),
                    "created_at": datetime.utcnow().isoformat()
                }
            }
            
            self.event_bus.publish('plan.proposed', data=plan_data)
            logger.info(f"✅ Plan proposed for task {task_id}")
            
            # Auto-approve the plan
            self.approve_plan(plan_data)
            
        except Exception as e:
            logger.error(f"❌ Error creating plan for task {task_id}: {e}", exc_info=True)
            error_data = {"task_id": task_id, "error": str(e), "goal": goal}
            self.event_bus.publish('plan.error', data=error_data)
        finally:
            # 确保在处理完成后释放锁
            self._safe_release_lock(lock_key, task_id)

    def _safe_release_lock(self, lock_key, task_id):
        """安全释放Redis锁"""
        try:
            redis_client.delete(lock_key)
            logger.info(f"✅ Released lock for task {task_id}.")
        except Exception as e:
            logger.error(f"❌ Failed to release lock for task {task_id}: {e}")

    def _publish_error_event(self, task_id, error_message, goal):
        """发布任务错误事件"""
        try:
            error_data = {
                "task_id": task_id,
                "error": error_message,
                "goal": goal,
                "timestamp": datetime.utcnow().isoformat(),
                "service": "agent-planner"
            }
            self.event_bus.publish('task.error', data=error_data)
            logger.info(f"📢 Published error event for task {task_id}")
        except Exception as e:
            logger.error(f"❌ Failed to publish error event for task {task_id}: {e}")

    def approve_plan(self, plan_data):
        """自动批准计划并发布 plan.approved 事件"""
        logger.info(f"✅ Auto-approving plan for task {plan_data['task_id']}")
        
        approved_data = plan_data.copy()
        approved_data['data']['approved_at'] = datetime.utcnow().isoformat()
        approved_data['data']['approved_by'] = 'auto-approval'
        
        self.event_bus.publish('plan.approved', data=approved_data)
        logger.info(f"📢 Published 'plan.approved' for task {plan_data['task_id']}")

    def log_event(self, event_type, data):
        """通用事件日志记录器"""
        logger.info(f"📢 Wildcard: Saw event '{event_type}'")

    def start(self):
        """启动 Planner Agent 的事件监听循环"""
        logger.info("🚀 Planner Agent is starting and listening for events...")
        self.event_bus.listen()

# Global agent instance for gunicorn workers
_agent_instance = None
listener_greenlet = None


def start_background_tasks():
    """Initialize and start background tasks for gunicorn workers"""
    global _agent_instance, listener_greenlet
    if _agent_instance is None:
        logger.info("🚀 Initializing PlannerAgent for worker process...")
        _agent_instance = PlannerAgent()
        # Start the event listener in a separate greenlet
        listener_greenlet = gevent.spawn(_agent_instance.start)
        listener_greenlet.start()
        logger.info("✅ PlannerAgent background tasks started successfully.")
    else:
        logger.info("ℹ️ PlannerAgent already initialized for this worker.")

if __name__ == "__main__":
    try:
        # This block is for direct execution, not for gunicorn
        agent = PlannerAgent()
        agent.start()
    except Exception as e:
        logger.critical(f"💥 A critical error occurred: {e}", exc_info=True)
        sys.exit(1)



