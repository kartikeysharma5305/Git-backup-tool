import sys
import os
import time
import queue

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from modules.debouncer import Debouncer
from modules.watcher import FileEvent

def test_debouncer():
    # Mock config with 1 second debounce
    config = {
        'watcher': {
            'debounce_ms': 1000
        }
    }
    
    raw_queue = queue.Queue()
    commit_queue = queue.Queue()
    
    debouncer = Debouncer(raw_queue, commit_queue, config)
    debouncer.start()
    
    print("Simulating rapid events for 'test.txt'...")
    path = "test.txt"
    
    # Send 5 events rapidly (every 0.1s)
    for i in range(5):
        print(f"Sending event {i+1}...")
        raw_queue.put(FileEvent(event_type='modified', src_path=path))
        time.sleep(0.1)
    
    # Wait for debounce to finish (1s + safety)
    print("Waiting for debounce period...")
    time.sleep(1.5)
    
    # Check output queue
    flushed_count = 0
    while not commit_queue.empty():
        event = commit_queue.get()
        print(f"Flushed: {event}")
        flushed_count += 1
    
    if flushed_count == 1:
        print("SUCCESS: 5 rapid events were debounced into 1.")
    else:
        print(f"FAILURE: Expected 1 event, but got {flushed_count}.")

    debouncer.stop()

if __name__ == "__main__":
    test_debouncer()
