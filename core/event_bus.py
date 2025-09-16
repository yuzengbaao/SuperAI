# src/core/event_bus.py

from collections import defaultdict
import threading
import redis
import json
import os
import logging
import time
from typing import Optional
import fnmatch

# 导入JSON格式化工具
try:
    from .json_formatter import StandardJSONFormatter, EventDataValidator
except ImportError:
    # 如果导入失败，使用标准JSON处理
    StandardJSONFormatter = None
    EventDataValidator = None

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class EventBus:
    """
    AGI Core Event Bus - Powered by Redis Pub/Sub.
    A decoupled, asynchronous publish/subscribe system for inter-microservice communication.
    This forms the distributed "telepathy network" or "nervous system" of the AGI.
    """
    def __init__(self):
        redis_host = os.environ.get('REDIS_HOST', 'agi-redis-lb')
        redis_port = int(os.environ.get('REDIS_PORT', 6379))
        
        try:
            # Use a connection pool for thread safety
            pool = redis.ConnectionPool(host=redis_host, port=redis_port, db=0, decode_responses=True)
            self.redis_client = redis.Redis(connection_pool=pool)
            self.redis_client.ping()
            logging.info(f"🧠 [Core] Event Bus connected to Redis at {redis_host}:{redis_port}.")
        except redis.ConnectionError as e:
            logging.error(f"❌ [Core] Failed to connect to Redis at {redis_host}:{redis_port}. Error: {e}")
            raise
            
        self.pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)
        self.listeners = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, listener):
        """
        Subscribe to an event type.
        :param event_type: The type of event (e.g., 'user_question_received').
        :param listener: A callable (function or method) to be invoked when the event is published.
        """
        with self._lock:
            # Check if listener is already subscribed to avoid duplicates
            if listener not in self.listeners[event_type]:
                self.listeners[event_type].append(listener)
                
                # Use psubscribe for wildcard patterns, subscribe for exact matches
                if '*' in event_type or '?' in event_type or '[' in event_type:
                    self.pubsub.psubscribe(event_type)
                    logging.info(f"  - Subscription successful: '{getattr(listener, '__module__', 'unknown')}.{getattr(listener, '__name__', 'unknown')}' is listening for pattern '{event_type}' (psubscribe).")
                else:
                    self.pubsub.subscribe(event_type)
                    logging.info(f"  - Subscription successful: '{getattr(listener, '__module__', 'unknown')}.{getattr(listener, '__name__', 'unknown')}' is listening for exact event '{event_type}' (subscribe).")
                    
                logging.info(f"  - Total listeners for '{event_type}': {len(self.listeners[event_type])}")
            else:
                logging.info(f"  - Listener '{getattr(listener, '__module__', 'unknown')}.{getattr(listener, '__name__', 'unknown')}' already subscribed to '{event_type}'.")

    def publish(self, event_type: str, data: Optional[dict] = None):
        """
        Publish an event to Redis.
        :param event_type: The type of event (the Redis channel).
        :param data: The data dictionary to pass to listeners (will be serialized to JSON).
        """
        if data is None:
            data = {}
        
        # 使用标准化JSON格式
        if StandardJSONFormatter and event_type == 'task.created':
            try:
                # 对任务事件进行格式化
                formatted_data = StandardJSONFormatter.format_task_event(data)
                message = StandardJSONFormatter.to_json_string(formatted_data)
                logging.info(f"📢 Using standardized JSON format for task event")
            except Exception as e:
                logging.warning(f"⚠️ Failed to format task event, using standard JSON: {e}")
                message = json.dumps(data)
        else:
            message = json.dumps(data)
        
        self.redis_client.publish(event_type, message)
        logging.info(f"📢 Published event '{event_type}' to Redis.")

    def _process_message(self, message):
        """
        Process a single message received from Redis.
        """
        msg_type = message.get('type')
        if msg_type not in ('message', 'pmessage'):
            return
            
        # Handle both regular messages and pattern messages
        if msg_type == 'pmessage':
            pattern = message.get('pattern')
            event_type = message.get('channel')
            payload = message.get('data', '{}')
            
            # For pmessage, we need to find all patterns that match the channel
            matching_patterns = [p for p in self.listeners if p != '*' and fnmatch.fnmatch(event_type, p)]
            logging.info(f"🔍 Processing pmessage: pattern='{pattern}', event_type='{event_type}', matching_patterns={matching_patterns}")
        else: # 'message'
            event_type = message.get('channel')
            payload = message.get('data', '{}')
            pattern = None
            matching_patterns = [event_type]
            logging.info(f"🔍 Processing message: event_type='{event_type}', matching_patterns={matching_patterns}")
            
        # 使用增强的JSON解析
        if StandardJSONFormatter:
            data = StandardJSONFormatter.safe_json_loads(payload)
            if data is None:
                logging.warning(f"⚠️ [EventBus] Could not decode JSON for event '{event_type}': {payload}")
                return
        else:
            try:
                data = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                logging.warning(f"⚠️ [EventBus] Could not decode JSON for event '{event_type}': {payload}")
                return
        
        # 验证事件数据格式
        if EventDataValidator and event_type == 'task.created':
            is_valid, error_msg = EventDataValidator.validate_task_event(data)
            if not is_valid:
                logging.warning(f"⚠️ [EventBus] Invalid task event data for '{event_type}': {error_msg}")
                return

        with self._lock:
            # Collect listeners from all matching patterns
            listeners_for_event = []
            for p in matching_patterns:
                listeners_for_event.extend(self.listeners.get(p, []))
                logging.info(f"🔍 Pattern '{p}' has {len(self.listeners.get(p, []))} listeners")

            wildcard_listeners = self.listeners.get('*', [])
            logging.info(f"🔍 Wildcard '*' has {len(wildcard_listeners)} listeners")
            
            # Use a set to ensure listeners are unique
            all_listeners = set(listeners_for_event + wildcard_listeners)
            
            logging.info(f"🔍 [EventBus] Processing event '{event_type}': matching_patterns={matching_patterns}, listeners_for_event={len(listeners_for_event)}, wildcard_listeners={len(wildcard_listeners)}, all_listeners={len(all_listeners)}")

        if not all_listeners:
            logging.warning(f"⚠️ [EventBus] No listeners found for event '{event_type}'")
            return

        for listener in all_listeners:
            try:
                logging.info(f"🔍 Calling listener '{getattr(listener, '__name__', 'unknown')}' for event '{event_type}'")
                # Call listener directly. If concurrency is needed, the listener itself
                # should handle spawning a thread.
                listener(event_type, data)
            except Exception as e:
                logging.error(f"❌ [EventBus] Error executing listener {getattr(listener, '__name__', 'unknown')}: {e}", exc_info=True)

    def listen(self):
        """
        Listens for messages in the foreground. This is a blocking operation.
        """
        logging.info("👂 [EventBus] Started listening for events in the foreground...")
        for message in self.pubsub.listen():
            self._process_message(message)

    def listen_in_background(self):
        """
        Starts a background thread to listen for messages.
        """
        logging.info("👂 [EventBus] Spawning event listener in a background thread...")
        listener_thread = threading.Thread(target=self.listen, daemon=True)
        listener_thread.start()
        return listener_thread

# --- For testing the EventBus within a single process ---
if __name__ == '__main__':
    
    def simple_listener(event_type, data):
        print(f"\n[Test Listener] Event received!")
        print(f"  - Type: {event_type}")
        print(f"  - Data: {data}")

    # 1. Create EventBus instance
    bus = EventBus()

    # 2. Subscribe
    bus.subscribe('test_event', simple_listener)
    bus.subscribe('*', simple_listener)

    # 3. Start listening in the background
    bus.listen_in_background()

    # 4. Publish an event
    print("\n--- Publishing a test event ---")
    test_data = {'message': 'Hello from the test block!', 'timestamp': time.time()}
    bus.publish('test_event', data=test_data)

    # Wait for the async event to be processed
    time.sleep(1)
    print("\n--- Test complete ---")
    input("Press Enter to exit...\n")
