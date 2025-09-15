import sys
import os
import time

# 将项目根目录添加到Python路径中，以便可以导入core模块
# This allows us to import modules from the 'core' directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.event_bus import EventBus

def main():
    """
    主函数，用于发布一个测试事件到Redis事件总线。
    """
    print("🚀 [Test Publisher] 准备发布测试事件...")
    
    # 1. 创建事件总线实例
    # 它会自动连接到在 docker-compose.yml 中定义的 'agi-redis-lb' 服务
    try:
        event_bus = EventBus()
        print("✅ [Test Publisher] 事件总线连接成功。")
    except Exception as e:
        print(f"❌ [Test Publisher] 无法连接到事件总线 (Redis): {e}")
        print("   请确保 Redis 服务 (agi-redis-lb) 正在运行。")
        return

    # 2. 定义要发布的事件
    event_type = "user_question_received"
    event_data = {
        "user_id": "test_user_001",
        "session_id": "session_xyz_789",
        "text": "你好，AGI！这是一个来自外部脚本的测试问题。",
        "timestamp": time.time()
    }

    # 3. 发布事件
    print(f"📢 [Test Publisher] 正在发布事件 '{event_type}'...")
    print(f"   - 数据: {event_data}")
    event_bus.publish(event_type, event_data)
    print("✅ [Test Publisher] 事件已成功发布到 Redis。")
    print("\n请检查 'agi-qwen-service' 服务的日志以确认事件是否被接收。")

if __name__ == '__main__':
    main()
