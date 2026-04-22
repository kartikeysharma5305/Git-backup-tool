import os
import json
import time
import queue
import signal
from watchdog.observers import Observer
from modules.watcher import BackupEventHandler
from modules.debouncer import Debouncer
from modules.engine import GitEngine
from modules.scheduler import RemotePushScheduler

class BackupController:
    """
    Orchestrator that ties all modules together:
    Watcher -> Debouncer -> Engine -> Scheduler
    """
    def __init__(self, repo_path, config):
        self.repo_path = os.path.abspath(repo_path)
        self.config = config
        
        self.raw_queue = queue.Queue()
        self.commit_queue = queue.Queue()
        
        # Modules
        self.handler = BackupEventHandler(self.raw_queue, self.config)
        self.debouncer = Debouncer(self.raw_queue, self.commit_queue, self.config)
        self.engine = GitEngine(self.commit_queue, self.repo_path, self.config)
        self.scheduler = RemotePushScheduler(self.repo_path, self.config)
        
        self.observer = Observer()
        self._running = False

    def start(self):
        print(f"Starting Backup Tool for: {self.repo_path}")
        
        # Start backend threads
        self.debouncer.start()
        self.engine.start()
        self.scheduler.start()
        
        # Start observer
        recursive = self.config.get('watcher', {}).get('recursive', True)
        self.observer.schedule(self.handler, self.repo_path, recursive=recursive)
        self.observer.start()
        
        self._running = True
        print("Monitoring active. Press Ctrl+C to stop (if running in foreground).")

    def stop(self):
        print("Stopping Backup Tool...")
        self.observer.stop()
        self.observer.join()
        
        self.debouncer.stop()
        self.engine.stop()
        self.scheduler.stop()
        
        self._running = False
        print("Stopped.")

    def run_forever(self):
        """Wait for signals to stop."""
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

def load_config(config_path):
    """Load TOML config. Using json as a fallback just in case or simple dict."""
    # Since we defined config.toml earlier, let's try to parse it.
    # We'll use tomllib if available (Python 3.11+) or a simple parser.
    try:
        import tomllib
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except:
        # Fallback to a hardcoded default if config missing/invalid
        return {
            'watcher': {'debounce_ms': 2000, 'recursive': True, 'max_file_size_mb': 50},
            'git': {'commit_message_template': '[BACKUP] {event_type}: {filename} @ {timestamp}', 'branch': 'main'},
            'remote': {'enabled': False}
        }

