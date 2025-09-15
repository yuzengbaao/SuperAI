import redis
import os
import time

def main():
    try:
        redis_host = os.getenv("REDIS_HOST", "agi-redis-lb")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        
        print(f"Connecting to Redis at {redis_host}:{redis_port}...")
        r = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
        
        pubsub = r.pubsub()
        
        channel = 'test_channel'
        print(f"Subscribing to channel '{channel}'...")
        pubsub.subscribe(channel)
        
        print("Subscription successful. Waiting for messages...")
        
        while True:
            message = pubsub.get_message()
            if message:
                print(f"Received message: {message}")
            time.sleep(0.1)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
