import sys
import os
import time
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.event_bus import EventBus

def on_any_event(event_type, event_data):
    """Callback function to log any event received."""
    logging.info(f"🕵️‍ [DEBUG LOGGER] Event Received! Type: '{event_type}', Data: {event_data}")

def main():
    """Main function to connect to the event bus and subscribe to all events."""
    logging.info("🚀 [DEBUG LOGGER] Starting up...")
    
    while True:
        try:
            event_bus = EventBus()
            logging.info("✅ [DEBUG LOGGER] Connected to Event Bus (Redis).")
            
            # Subscribe to all events using a wildcard
            event_bus.subscribe('*', on_any_event)
            
            logging.info("👂 [DEBUG LOGGER] Subscribed to all events ('*'). Listening indefinitely...")
            
            # The listen method in EventBus now blocks, so we just call it.
            # This will keep the script alive and processing events.
            event_bus.listen()
            
        except KeyboardInterrupt:
            logging.info("🛑 [DEBUG LOGGER] Shutdown signal received.")
            break
        except Exception as e:
            logging.error(f"❌ [DEBUG LOGGER] An error occurred: {e}. Reconnecting in 10 seconds...")
            time.sleep(10)

if __name__ == '__main__':
    main()
