import redis
import os
import json

def main():
    try:
        redis_host = os.getenv("REDIS_HOST", "agi-redis-lb")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        
        print(f"Connecting to Redis at {redis_host}:{redis_port}...")
        r = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
        
        print("Pinging Redis...")
        r.ping()
        print("Redis ping successful.")
        
        channel = 'test_channel'
        message_data = {"text": "hello from simple publisher"}
        message = json.dumps(message_data)
        
        print(f"Publishing message '{message}' to channel '{channel}'...")
        result = r.publish(channel, message)
        print(f"Publish command sent. Number of clients that received the message: {result}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
