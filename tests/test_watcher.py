import os
import queue
from pathlib import Path
from types import SimpleNamespace

# Add src to path
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from modules.watcher import BackupEventHandler, FileEvent


def _event(
    event_type: str,
    src_path: str,
    is_directory: bool = False,
    dest_path: str | None = None,
):
    return SimpleNamespace(
        event_type=event_type,
        src_path=src_path,
        dest_path=dest_path,
        is_directory=is_directory,
    )


def test_file_event_timestamp_is_unique_per_instance():
    first = FileEvent(event_type="created", src_path="a.txt")
    second = FileEvent(event_type="created", src_path="b.txt")

    assert first.timestamp
    assert second.timestamp
    assert first.timestamp <= second.timestamp


def test_watcher_filters_and_enqueues_supported_events(tmp_path: Path):
    cfg = {
        "watcher": {
            "max_file_size_mb": 1,
            "exclude_extensions": [".tmp", ".swp"],
            "recursive": True,
        }
    }
    q = queue.Queue()
    handler = BackupEventHandler(q, cfg)

    tracked_file = tmp_path / "tracked.txt"
    tracked_file.write_text("hello", encoding="utf-8")

    ignored_file = tmp_path / "ignore.tmp"
    ignored_file.write_text("ignore", encoding="utf-8")

    handler.on_created(_event("created", str(tracked_file)))
    handler.on_modified(_event("modified", str(ignored_file)))

    item = q.get(timeout=1)
    assert item.event_type == "created"
    assert item.src_path.endswith("tracked.txt")

    assert q.empty()


def test_watcher_ignores_git_directory_events(tmp_path: Path):
    cfg = {"watcher": {"max_file_size_mb": 50, "exclude_extensions": []}}
    q = queue.Queue()
    handler = BackupEventHandler(q, cfg)

    git_path = tmp_path / ".git" / "objects" / "ab" / "blob"
    git_path.parent.mkdir(parents=True, exist_ok=True)
    git_path.write_text("x", encoding="utf-8")

    handler.on_created(_event("created", str(git_path)))
    assert q.empty()


def test_watcher_handles_move_events(tmp_path: Path):
    cfg = {"watcher": {"max_file_size_mb": 50, "exclude_extensions": []}}
    q = queue.Queue()
    handler = BackupEventHandler(q, cfg)

    src = tmp_path / "old.txt"
    dst = tmp_path / "new.txt"
    src.write_text("data", encoding="utf-8")

    handler.on_moved(_event("moved", str(src), dest_path=str(dst)))

    moved = q.get(timeout=1)
    assert moved.event_type == "moved"
    assert moved.src_path.endswith("old.txt")
    assert moved.dest_path.endswith("new.txt")
