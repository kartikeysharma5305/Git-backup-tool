import sys
import os
import time
import queue
from watchdog.observers import Observer

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from modules.watcher import BackupEventHandler

def test_watcher():
    # Mock config
    config = {
        'watcher': {
            'max_file_size_mb': 50,
            'exclude_extensions': ['.swp', '.tmp'],
            'recursive': True
        }
    }
    
    event_queue = queue.Queue()
    handler = BackupEventHandler(event_queue, config)
    
    observer = Observer()
    target_path = os.path.abspath("./test_watch_dir")
    
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    
    observer.schedule(handler, target_path, recursive=True)
    observer.start()
    
    print(f"Monitoring {target_path}...")
    print("Create, modify, or delete files in that directory to see events.")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            try:
                event = event_queue.get(timeout=1)
                print(f"Captured: {event}")
            except queue.Empty:
                pass
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    test_watcher()
