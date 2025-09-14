#!/usr/bin/env python3
"""
多智能体协作任务启动脚本
用于测试多智能体协作工作流程
"""

import sys
import os
import uuid
import time
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.event_bus import EventBus

def main():
    """
    启动多智能体协作任务的主函数
    """
    print("🚀 [Multi-Agent Task Starter] 启动多智能体协作任务...")
    
    try:
        # 连接事件总线
        event_bus = EventBus()
        print("✅ [Multi-Agent Task Starter] 事件总线连接成功")
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        session_id = "multi_agent_demo_001"
        
        # 定义任务目标
        goal = "写一首关于星际探索的五言绝句"
        
        print(f"📋 [Multi-Agent Task Starter] 创建任务:")
        print(f"   - 任务ID: {task_id}")
        print(f"   - 会话ID: {session_id}")
        print(f"   - 目标: {goal}")
        
        # 准备任务数据
        task_data = {
            "task_id": task_id,
            "session_id": session_id,
            "data": {
                "goal": goal,
                "created_at": datetime.utcnow().isoformat(),
                "priority": "normal",
                "requester": "multi_agent_demo"
            }
        }
        
        # 发布任务创建事件
        print("📢 [Multi-Agent Task Starter] 发布 'task.created' 事件...")
        event_bus.publish('task.created', data=task_data)
        
        print("✅ [Multi-Agent Task Starter] 任务已创建并发布到事件总线")
        print("")
        print("🔍 [Multi-Agent Task Starter] 预期的协作流程:")
        print("   1. agent-planner 接收 'task.created' 事件")
        print("   2. agent-planner 分析任务并创建执行计划")
        print("   3. agent-planner 发布 'plan.proposed' 事件")
        print("   4. agent-planner 自动批准计划，发布 'plan.approved' 事件")
        print("   5. agent-executor 接收 'plan.approved' 事件")
        print("   6. agent-executor 逐步执行计划")
        print("   7. agent-executor 调用 vLLM 服务生成诗歌")
        print("   8. agent-executor 发布 'task.completed' 事件")
        print("")
        print("📊 [Multi-Agent Task Starter] 监控建议:")
        print("   - 查看 agent-planner 日志: docker-compose logs -f agent-planner")
        print("   - 查看 agent-executor 日志: docker-compose logs -f agent-executor")
        print("   - 查看 vllm-service 日志: docker-compose logs -f vllm-service")
        print("")
        print("🎯 [Multi-Agent Task Starter] 任务启动完成！")
        
        return task_id
        
    except Exception as e:
        print(f"❌ [Multi-Agent Task Starter] 启动任务时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_custom_task(goal, session_id=None):
    """
    创建自定义任务
    """
    if not session_id:
        session_id = f"custom_{int(time.time())}"
        
    task_id = str(uuid.uuid4())
    
    try:
        event_bus = EventBus()
        
        task_data = {
            "task_id": task_id,
            "session_id": session_id,
            "data": {
                "goal": goal,
                "created_at": datetime.utcnow().isoformat(),
                "priority": "normal",
                "requester": "custom_task"
            }
        }
        
        event_bus.publish('task.created', data=task_data)
        print(f"✅ 自定义任务已创建: {task_id}")
        print(f"   目标: {goal}")
        
        return task_id
        
    except Exception as e:
        print(f"❌ 创建自定义任务失败: {e}")
        return None

if __name__ == '__main__':
    # 检查命令行参数
    if len(sys.argv) > 1:
        # 自定义任务模式
        custom_goal = " ".join(sys.argv[1:])
        print(f"🎯 创建自定义任务: {custom_goal}")
        task_id = create_custom_task(custom_goal)
    else:
        # 默认演示任务
        task_id = main()
    
    if task_id:
        print(f"\n🆔 任务ID: {task_id}")
        print("\n💡 提示: 您可以使用以下命令创建自定义任务:")
        print("   python scripts/start_multi_agent_task.py '您的自定义任务目标'")
    else:
        sys.exit(1)