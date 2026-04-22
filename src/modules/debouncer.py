import threading
import time
import queue
from typing import Dict, Any

class Debouncer(threading.Thread):
    """
    Thread that batches multiple rapid events for the same file path 
    into a single event to avoid commit log pollution.
    """
    def __init__(self, input_queue: queue.Queue, output_queue: queue.Queue, config: Dict[str, Any]):
        super().__init__(daemon=True)
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.config = config
        self.debounce_ms = config.get('watcher', {}).get('debounce_ms', 2000)
        self.debounce_sec = self.debounce_ms / 1000.0
        
        # Dictionary to track {path: (last_event, timer)}
        self.pending_events = {}
        self.lock = threading.Lock()
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            try:
                # Wait for an event with a small timeout to allow checking stop_event
                event = self.input_queue.get(timeout=0.1)
                self._handle_event(event)
            except queue.Empty:
                continue

    def _handle_event(self, event):
        path = event.src_path
        
        with self.lock:
            # If there's already a timer for this path, cancel it
            if path in self.pending_events:
                _, timer = self.pending_events[path]
                timer.cancel()

            # Start a new timer
            # We use a lambda to ensure the latest event state is passed
            timer = threading.Timer(self.debounce_sec, self._flush_event, [path])
            self.pending_events[path] = (event, timer)
            timer.start()

    def _flush_event(self, path):
        with self.lock:
            if path in self.pending_events:
                event, _ = self.pending_events.pop(path)
                self.output_queue.put(event)

    def stop(self):
        self._stop_event.set()
        with self.lock:
            for _, timer in self.pending_events.values():
                timer.cancel()
        self.join()
