# Git-based File Backup Tool

Automate local file changes with Git-powered versioned backups. This tool monitors a directory in real-time and automatically creates Git commits whenever files are created, modified, or deleted.

## Features
- **Real-time Monitoring**: Uses `watchdog` to detect file system events instantly.
- **Intelligent Debouncing**: Batches rapid changes (like auto-saves) to keep history clean.
- **Git Powered**: Leverages Git for efficient, delta-based versioning and full rollback capability.
- **Remote Sync**: Automatically pushes local backups to GitHub/GitLab (optional).
- **Dual Interface**: Full-featured CLI for power users and a simple GUI (Tkinter) for ease of use.

## Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure `git` is installed and in your system PATH.

## Usage (CLI)
- **Initialize a folder**:
  ```bash
  python src/gitbackup.py init [folder_path]
  ```
- **Start the backup service**:
  ```bash
  python src/gitbackup.py start
  ```
- **View backup history**:
  ```bash
  python src/gitbackup.py log --n 20
  ```
- **Restore a file**:
  ```bash
  python src/gitbackup.py restore <file_path> [--commit <hash>]
  ```
- **Check status**:
  ```bash
  python src/gitbackup.py status
  ```

## Usage (GUI)
Launch the graphical dashboard:
```bash
python src/gitbackup.py gui
```

## Configuration
Settings are managed in `config/config.toml`:
- `debounce_ms`: Buffer time before committing rapid changes.
- `max_file_size_mb`: Files larger than this are ignored.
- `remote.enabled`: Toggle automatic pushes to GitHub.

## Development
- **Source Code**: All logic is in the `src/` directory.
- **Tests**: Run scripts in the `tests/` folder to verify individual modules.
- **Build**: Use `pyinstaller` to create a standalone binary:
  ```bash
  pyinstaller --onefile --noconsole src/gitbackup.py
  ```
