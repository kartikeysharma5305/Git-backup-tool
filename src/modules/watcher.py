from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import os
from watchdog.events import FileSystemEventHandler

@dataclass
class FileEvent:
    """Data class to represent a file system event."""
    event_type: str  # 'created', 'modified', 'deleted', 'moved'
    src_path: str
    dest_path: Optional[str] = None
    timestamp: str = datetime.utcnow().isoformat()
    is_directory: bool = False

class BackupEventHandler(FileSystemEventHandler):
    """
    Custom event handler that captures file system events and
    converts them into FileEvent objects.
    """
    def __init__(self, queue, config):
        self.queue = queue
        self.config = config
        self.max_size_bytes = config.get('watcher', {}).get('max_file_size_mb', 50) * 1024 * 1024
        self.exclude_exts = set(config.get('watcher', {}).get('exclude_extensions', []))

    def _should_ignore(self, path):
        """Check if the file should be ignored based on path, size, or extension."""
        # --- CRITICAL: Never watch anything inside a .git/ folder ---
        # Normalize separators and check every path segment
        normalized = path.replace('\\', '/')
        if '/.git/' in normalized or normalized.endswith('/.git'):
            return True
        # Also catch Windows absolute paths like C:\project\.git\...
        if os.sep + '.git' + os.sep in path or path.endswith(os.sep + '.git'):
            return True

        # Ignore directories (Git tracks files, not folders)
        if os.path.isdir(path):
            return True

        # Check extension against exclusion list
        _, ext = os.path.splitext(path)
        if ext in self.exclude_exts:
            return True

        # Check file size (only for existing files)
        try:
            if os.path.exists(path) and os.path.getsize(path) > self.max_size_bytes:
                return True
        except (OSError, FileNotFoundError):
            pass

        return False

    def on_created(self, event):
        if not event.is_directory and not self._should_ignore(event.src_path):
            file_event = FileEvent(
                event_type='created',
                src_path=event.src_path,
                is_directory=event.is_directory
            )
            self.queue.put(file_event)

    def on_modified(self, event):
        if not event.is_directory and not self._should_ignore(event.src_path):
            file_event = FileEvent(
                event_type='modified',
                src_path=event.src_path,
                is_directory=event.is_directory
            )
            self.queue.put(file_event)

    def on_deleted(self, event):
        # We can't check size/ext easily for deleted files if we don't have a cache,
        # but we can check the extension from the path.
        if not event.is_directory and not self._should_ignore(event.src_path):
            file_event = FileEvent(
                event_type='deleted',
                src_path=event.src_path,
                is_directory=event.is_directory
            )
            self.queue.put(file_event)

    def on_moved(self, event):
        if not event.is_directory and not self._should_ignore(event.dest_path):
            file_event = FileEvent(
                event_type='moved',
                src_path=event.src_path,
                dest_path=event.dest_path,
                is_directory=event.is_directory
            )
            self.queue.put(file_event)
