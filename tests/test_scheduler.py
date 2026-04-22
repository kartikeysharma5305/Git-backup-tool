import os
from pathlib import Path

# Add src to path
import sys

import git

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from modules.scheduler import RemotePushScheduler


def test_scheduler_commit_count_and_push(tmp_path: Path):
    base_dir = tmp_path / "scheduler"
    local_dir = base_dir / "local"
    remote_dir = base_dir / "remote.git"

    local_dir.mkdir(parents=True, exist_ok=True)
    git.Repo.init(str(remote_dir), bare=True)

    local_repo = git.Repo.init(str(local_dir), initial_branch="main")
    local_repo.create_remote("origin", str(remote_dir))

    init_file = local_dir / "init.txt"
    init_file.write_text("init", encoding="utf-8")
    local_repo.index.add(["init.txt"])
    local_repo.index.commit("Initial commit")
    local_repo.remote("origin").push("main:main")

    file_1 = local_dir / "file_1.txt"
    file_1.write_text("content 1", encoding="utf-8")
    local_repo.index.add(["file_1.txt"])
    local_repo.index.commit("Commit 1")

    cfg = {
        "remote": {
            "enabled": True,
            "push_interval_commits": 1,
            "push_interval_minutes": 60,
        },
        "git": {"branch": "main"},
    }

    scheduler = RemotePushScheduler(str(local_dir), cfg)
    assert scheduler._get_commit_count_since_last_push(local_repo) == 1

    scheduler._perform_push(local_repo)

    remote_repo = git.Repo(str(remote_dir))
    remote_commits = list(remote_repo.iter_commits("main"))
    assert len(remote_commits) == 2

    local_repo.close()
    remote_repo.close()
