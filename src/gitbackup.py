import argparse
import sys
import os
import git
import time
from modules.controller import BackupController, load_config

def find_repo_root():
    """Find the root of the current project or fallback to CWD."""
    try:
        repo = git.Repo(".", search_parent_directories=True)
        return repo.working_tree_dir
    except:
        return os.getcwd()

def main():
    parser = argparse.ArgumentParser(description="Git-based File Backup Tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Init
    init_parser = subparsers.add_parser("init", help="Initialize a backup repository")
    init_parser.add_argument("folder", nargs="?", default=".", help="Folder to monitor (default: current)")

    # Start
    subparsers.add_parser("start", help="Start the backup watcher")

    # Stop
    subparsers.add_parser("stop", help="Stop the backup watcher")

    # Status
    subparsers.add_parser("status", help="Show current status")

    # GUI
    subparsers.add_parser("gui", help="Launch the graphical dashboard")

    # Log
    log_parser = subparsers.add_parser("log", help="Display the last N commit messages")
    log_parser.add_argument("--n", type=int, default=10, help="Number of commits to show")

    # Restore
    restore_parser = subparsers.add_parser("restore", help="Restore a file to a specific commit")
    restore_parser.add_argument("file", help="Path to the file to restore")
    restore_parser.add_argument("--commit", help="Commit hash (optional, defaults to last change for this file)")

    args = parser.parse_args()

    # Load config
    config_dir = os.path.join(os.path.dirname(__file__), "..", "config")
    config_path = os.path.join(config_dir, "config.toml")
    config = load_config(config_path)

    repo_root = find_repo_root()

    if args.command == "init":
        target = os.path.abspath(args.folder)
        if not os.path.exists(os.path.join(target, ".git")):
            print(f"Initializing Git repository in {target}...")
            git.Repo.init(target)
            print("Done.")
        else:
            print(f"Directory {target} is already a Git repository.")

    elif args.command == "start":
        # Simplified: Runs in foreground for now
        controller = BackupController(repo_root, config)
        controller.start()
        controller.run_forever()

    elif args.command == "status":
        try:
            repo = git.Repo(repo_root)
            print(f"Monitoring Repository: {repo_root}")
            print(f"Current Branch: {repo.active_branch.name}")
            print(f"Last Commit: {list(repo.iter_commits(max_count=1))[0].summary}")
        except:
            print("Not a valid Git repository. Run 'gitbackup init' first.")

    elif args.command == "gui":
        from modules.gui import run_gui
        run_gui()

    elif args.command == "log":
        try:
            repo = git.Repo(repo_root)
            commits = list(repo.iter_commits(max_count=args.n))
            print(f"--- Last {args.n} Backups ---")
            for c in commits:
                print(f"[{c.hexsha[:7]}] {c.summary} ({time.ctime(c.committed_date)})")
        except:
            print("Error reading git log.")

    elif args.command == "restore":
        try:
            repo = git.Repo(repo_root)
            file_path = args.file
            rev = args.commit if args.commit else "HEAD"
            
            # Checkout specific version
            repo.git.checkout(rev, "--", file_path)
            print(f"Restored {file_path} from {rev}.")
        except Exception as e:
            print(f"Failed to restore: {e}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
