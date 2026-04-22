import sys
import os
import time
import shutil
import git

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from modules.scheduler import RemotePushScheduler

def test_scheduler():
    # Setup local repo and "remote" repo on disk
    base_dir = os.path.abspath("./test_scheduler")
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir)
    
    local_dir = os.path.join(base_dir, "local")
    remote_dir = os.path.join(base_dir, "remote.git")
    
    os.makedirs(local_dir)
    # Initialize bare remote repo
    git.Repo.init(remote_dir, bare=True)
    
    # Setup local repo
    local_repo = git.Repo.init(local_dir)
    local_repo.create_remote('origin', remote_dir)
    
    # Create initial commit and push (to set up tracking)
    with open(os.path.join(local_dir, "init.txt"), 'w') as f:
        f.write("init")
    local_repo.index.add(["init.txt"])
    local_repo.index.commit("Initial commit")
    local_repo.remote('origin').push('main:main')
    local_repo.git.branch('--set-upstream-to=origin/main', 'main')
    
    # Config for scheduler: push after 2 commits
    config = {
        'remote': {
            'enabled': True,
            'push_interval_commits': 2,
            'push_interval_minutes': 1
        },
        'git': {
            'branch': 'main'
        }
    }
    
    scheduler = RemotePushScheduler(local_dir, config)
    scheduler.start()
    
    print("Simulating 2 new local commits...")
    for i in range(2):
        with open(os.path.join(local_dir, f"file_{i}.txt"), 'w') as f:
            f.write(f"content {i}")
        local_repo.index.add([f"file_{i}.txt"])
        local_repo.index.commit(f"Commit {i}")
        time.sleep(1)
        
    print("Waiting for scheduler to detect threshold and push...")
    time.sleep(40) # scheduler checks every 30s
    
    # Verify remote repo has the commits
    remote_repo = git.Repo(remote_dir)
    remote_commits = list(remote_repo.iter_commits('main'))
    print(f"Remote commit count: {len(remote_commits)}")
    
    if len(remote_commits) >= 3: # 1 (init) + 2 (test)
        print("SUCCESS: Scheduler automatically pushed to remote.")
    else:
        print("FAILURE: Remote repository not updated.")
        
    scheduler.stop()
    # shutil.rmtree(base_dir)

if __name__ == "__main__":
    test_scheduler()
