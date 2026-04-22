import os
import git
import threading
import queue
from datetime import datetime
from typing import Dict, Any

class GitEngine(threading.Thread):
    """
    Consumer thread that takes debounced events and executes 
    Git add/rm and commit operations using GitPython.
    """
    def __init__(self, commit_queue: queue.Queue, repo_path: str, config: Dict[str, Any]):
        super().__init__(daemon=True)
        self.commit_queue = commit_queue
        self.repo_path = os.path.abspath(repo_path)
        self.config = config
        self.msg_template = config.get('git', {}).get(
            'commit_message_template', 
            '[BACKUP] {event_type}: {filename} @ {timestamp}'
        )
        self._stop_event = threading.Event()
        self.repo = self._init_repo()

    def _init_repo(self) -> git.Repo:
        """Initialize the repository if it doesn't exist."""
        if not os.path.exists(os.path.join(self.repo_path, '.git')):
            print(f"Initializing new Git repository at {self.repo_path}")
            repo = git.Repo.init(self.repo_path)
            # Create initial commit if empty
            readme_path = os.path.join(self.repo_path, 'README.md')
            if not os.path.exists(readme_path):
                with open(readme_path, 'w') as f:
                    f.write("# Git-based File Backup\nAutomated versioned backups.")
                repo.index.add(['README.md'])
                repo.index.commit("[BACKUP] Repository initialized")
            return repo
        else:
            return git.Repo(self.repo_path)

    def run(self):
        while not self._stop_event.is_set():
            try:
                event = self.commit_queue.get(timeout=0.1)
                self._process_event(event)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in Git Engine: {e}")

    def _process_event(self, event):
        """Execute the git operations for a given event."""
        # Convert absolute path to relative path for Git
        try:
            rel_path = os.path.relpath(event.src_path, self.repo_path)
            
            if event.event_type in ['created', 'modified']:
                if os.path.exists(event.src_path):
                    self.repo.index.add([rel_path])
                else:
                    return # Race condition: file deleted before we could add it

            elif event.event_type == 'deleted':
                try:
                    # Use git rm --cached to properly stage the deletion
                    self.repo.git.rm('--cached', '--ignore-unmatch', rel_path)
                    # If the file was never tracked, the index won't change — skip commit
                    if not self.repo.index.diff("HEAD"):
                        return
                except git.GitCommandError:
                    return

            elif event.event_type == 'moved':
                rel_dest = os.path.relpath(event.dest_path, self.repo_path)
                try:
                    self.repo.index.remove([rel_path])
                except git.GitCommandError:
                    pass
                if os.path.exists(event.dest_path):
                    self.repo.index.add([rel_dest])
                
            # Create commit
            filename = os.path.basename(event.src_path)
            timestamp = datetime.now().isoformat()
            message = self.msg_template.format(
                event_type=event.event_type.upper(),
                filename=filename,
                timestamp=timestamp
            )
            
            self.repo.index.commit(message)
            # print(f"Committed: {message}")
            
        except ValueError:
            # Path not in repo directory
            pass
        except Exception as e:
            print(f"Failed to commit change for {event.src_path}: {e}")

    def stop(self):
        self._stop_event.set()
        self.join()
