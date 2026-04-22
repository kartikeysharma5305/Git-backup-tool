import sys
import os
import time
import queue
import shutil
import git

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from modules.engine import GitEngine
from modules.watcher import FileEvent

def test_engine():
    repo_dir = os.path.abspath("./test_repo")
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)
    os.makedirs(repo_dir)
    
    commit_queue = queue.Queue()
    config = {
        'git': {
            'commit_message_template': '[TEST] {event_type}: {filename} @ {timestamp}'
        }
    }
    
    engine = GitEngine(commit_queue, repo_dir, config)
    engine.start()
    
    # 1. Test Created
    print("Testing 'created' event...")
    test_file = os.path.join(repo_dir, "hello.txt")
    with open(test_file, 'w') as f:
        f.write("Hello World")
    
    commit_queue.put(FileEvent(event_type='created', src_path=test_file))
    time.sleep(1) # Give engine time to process
    
    # Check git log
    repo = git.Repo(repo_dir)
    commits = list(repo.iter_commits())
    print(f"Latest commit: {commits[0].message}")
    
    if "CREATED: hello.txt" in commits[0].message:
        print("SUCCESS: 'created' event committed.")
    else:
        print("FAILURE: commit message mismatch.")

    # 2. Test Modified
    print("\nTesting 'modified' event...")
    with open(test_file, 'a') as f:
        f.write("\nUpdated content")
    
    commit_queue.put(FileEvent(event_type='modified', src_path=test_file))
    time.sleep(1)
    
    commits = list(repo.iter_commits())
    print(f"Latest commit: {commits[0].message}")
    if "MODIFIED: hello.txt" in commits[0].message:
        print("SUCCESS: 'modified' event committed.")
    
    # 3. Test Deleted
    print("\nTesting 'deleted' event...")
    os.remove(test_file)
    commit_queue.put(FileEvent(event_type='deleted', src_path=test_file))
    time.sleep(1)
    
    commits = list(repo.iter_commits())
    print(f"Latest commit: {commits[0].message}")
    if "DELETED: hello.txt" in commits[0].message:
        print("SUCCESS: 'deleted' event committed.")
        
    engine.stop()
    # shutil.rmtree(repo_dir)

if __name__ == "__main__":
    test_engine()
