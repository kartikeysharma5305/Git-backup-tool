import threading
import time
import git
from typing import Dict, Any

class RemotePushScheduler(threading.Thread):
    """
    Background thread that periodically pushes local commits to a 
    remote repository based on time or commit count thresholds.
    """
    def __init__(self, repo_path: str, config: Dict[str, Any]):
        super().__init__(daemon=True)
        self.repo_path = repo_path
        self.config = config
        
        remote_cfg = config.get('remote', {})
        self.enabled = remote_cfg.get('enabled', False)
        self.push_interval_commits = remote_cfg.get('push_interval_commits', 10)
        self.push_interval_minutes = remote_cfg.get('push_interval_minutes', 30)
        self.branch = config.get('git', {}).get('branch', 'main')
        
        self._stop_event = threading.Event()
        self.last_push_time = time.time()
        self.last_pushed_commit = None

    def run(self):
        if not self.enabled:
            print("Remote push is disabled in config.")
            return

        while not self._stop_event.is_set():
            try:
                repo = git.Repo(self.repo_path)
                
                # Check if we have an 'origin' remote
                if 'origin' not in repo.remotes:
                    time.sleep(60) # Wait a bit and check again
                    continue
                
                current_commit = repo.head.commit
                
                # Threshold checks
                commits_since_push = self._get_commit_count_since_last_push(repo)
                minutes_since_push = (time.time() - self.last_push_time) / 60.0
                
                should_push = False
                if commits_since_push >= self.push_interval_commits:
                    should_push = True
                    # print(f"Threshold reached: {commits_since_push} new commits.")
                elif minutes_since_push >= self.push_interval_minutes and commits_since_push > 0:
                    should_push = True
                    # print(f"Threshold reached: {minutes_since_push:.1f} minutes elapsed.")
                
                if should_push:
                    self._perform_push(repo)
                    self.last_push_time = time.time()
                    self.last_pushed_commit = current_commit
                
            except Exception as e:
                # print(f"Remote push scheduler error: {e}")
                pass
                
            # Sleep for a bit before checking again
            time.sleep(30)

    def _get_commit_count_since_last_push(self, repo: git.Repo) -> int:
        """Count how many commits are on local branch that aren't on remote origin."""
        try:
            # git rev-list --count origin/main..main
            count_str = repo.git.rev_list('--count', f'origin/{self.branch}..{self.branch}')
            return int(count_str)
        except git.GitCommandError:
            # Remote might not exist yet or branch mismatch
            return 0

    def _perform_push(self, repo: git.Repo):
        """Execute the git push command with basic retry logic."""
        retries = 3
        backoff = 5
        
        for i in range(retries):
            try:
                origin = repo.remote(name='origin')
                origin.push(self.branch)
                # print("Successfully pushed to remote.")
                return
            except Exception as e:
                # print(f"Push attempt {i+1} failed: {e}")
                if i < retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
        
        # print("Final push attempt failed. Will retry in next cycle.")

    def stop(self):
        self._stop_event.set()
        self.join()
