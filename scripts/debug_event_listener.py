import sys
import os
import time

# Add the project root to the Python path to allow importing the core module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.event_bus import EventBus

def on_event(event_type, event_data):
    """
    Callback function to handle received events.
    """
    print(f"🕵️‍ [Debug Listener] Event Received!")
    print(f"   - Type: {event_type}")
    print(f"   - Data: {event_data}")
    print("-" * 30)

def main():
    """
    Main function to subscribe to all events and listen indefinitely.
    """
    print("🚀 [Debug Listener] Starting up...")
    
    try:
        event_bus = EventBus()
        print("✅ [Debug Listener] Event bus connected successfully.")
    except Exception as e:
        print(f"❌ [Debug Listener] Could not connect to event bus (Redis): {e}")
        return

    # Subscribe to all events
    event_bus.subscribe('*', on_event)
    
    print("👂 [Debug Listener] Subscribed to all events ('*'). Listening...")
    print("   (Waiting for events. Press Ctrl+C to exit)")

    # Start listening for events - this is the missing piece!
    try:
        event_bus.listen()  # This will block and process Redis messages
    except KeyboardInterrupt:
        print("\n🛑 [Debug Listener] Shutting down.")

if __name__ == '__main__':
    main()
