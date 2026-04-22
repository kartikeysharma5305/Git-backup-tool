# BackTrack Desk

BackTrack Desk is a desktop Git backup assistant built with Tkinter. It watches a selected project folder and automatically creates Git commits for file changes, so you can recover earlier versions quickly.

## What It Does

- Watches your folder in real time using `watchdog`
- Debounces rapid file saves to avoid noisy commit history
- Creates automatic Git commits for create/modify/delete/move events
- Shows commit history in a GUI timeline
- Restores to an earlier commit from the History tab
- Optionally pushes to a remote repository on a schedule

## Tech Stack

- Python 3
- Tkinter GUI
- GitPython
- watchdog

## Project Structure

- `src/gitbackup.py`: CLI entrypoint and command routing
- `src/modules/gui.py`: BackTrack Desk GUI
- `src/modules/controller.py`: orchestrates watcher, debouncer, engine, scheduler
- `src/modules/watcher.py`: filesystem event capture/filtering
- `src/modules/debouncer.py`: event coalescing logic
- `src/modules/engine.py`: Git add/rm/commit engine
- `src/modules/scheduler.py`: optional remote push scheduler
- `config/config.toml`: runtime configuration
- `tests/`: automated test suite

## Setup

1. Clone this repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure Git is installed and available in PATH.

## Run The App (GUI)

From project root:

```bash
python src/gitbackup.py gui
```

If you use this workspace virtual environment on Windows:

```bash
"c:/VCS project/.venv/Scripts/python.exe" src/gitbackup.py gui
```

## How To Use

1. Open BackTrack Desk.
2. Click **Browse** and choose your project folder.
3. Click **Start watching**.
4. Edit files in that folder.
5. Check **Recent activity** and **Commit history** to verify backups.
6. To restore, open **History**, select a commit, then click **Roll back selected**.

## Demo Script (2 Minutes)

Use this flow for class presentation:

1. **Intro (15s)**

- "This is BackTrack Desk, a desktop backup tool that uses Git in the background."

2. **Problem statement (15s)**

- "Developers often overwrite files by mistake. This tool creates automatic versioned backups while you work."

3. **Start demo (20s)**

- Launch GUI and select a project folder.
- Click **Start watching**.

4. **Trigger backup (25s)**

- Open any file in the watched folder, edit and save it.
- Show **Recent activity** updating in real time.

5. **Show history (20s)**

- Open **Commit history** and show the new commit entry.

6. **Restore flow (20s)**

- Select an older commit and click **Roll back selected**.
- Explain this restores the project state to that version.

7. **Close (15s)**

- "So BackTrack Desk gives automatic local backups, quick rollback, and optional remote push."

Demo tips:

- Keep one text file ready for quick edits.
- Use short edits like adding one line so commit changes are obvious.
- If needed, click **Refresh history** before showing the latest commit.

## CLI Commands

- Initialize repository:
  ```bash
  python src/gitbackup.py init [folder_path]
  ```
- Start watcher in terminal:
  ```bash
  python src/gitbackup.py start
  ```
- Check repository status:
  ```bash
  python src/gitbackup.py status
  ```
- Show latest commits:
  ```bash
  python src/gitbackup.py log --n 20
  ```
- Restore a file from commit/HEAD:
  ```bash
  python src/gitbackup.py restore <file_path> [--commit <hash>]
  ```

## Configuration

Edit `config/config.toml`:

- `watcher.target_directory`: default folder to watch
- `watcher.debounce_ms`: debounce window in milliseconds
- `watcher.max_file_size_mb`: ignore files larger than this limit
- `watcher.exclude_extensions`: extension filters
- `remote.enabled`: enable/disable remote auto-push
- `remote.remote_url`: remote repo URL
- `remote.push_interval_commits`: push after N commits
- `remote.push_interval_minutes`: push after N minutes

## Testing

Run all tests:

```bash
python -m pytest -q
```

## Packaging (Optional)

Create a single-file Windows executable:

```bash
python -m pyinstaller --onefile --noconsole --name BackTrackDesk src/gitbackup.py
```

Output binary:

- `dist/BackTrackDesk.exe`

## Free Distribution Options

- GitHub Releases (recommended)
- Itch.io (download page style)
- SourceForge
