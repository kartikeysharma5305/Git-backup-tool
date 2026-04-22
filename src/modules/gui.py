import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import git

from modules.controller import BackupController, load_config


class BackupGUI:
    """Desktop dashboard for managing automated Git backups."""

    def __init__(self, root):
        self.root = root
        self.root.title("BackTrack Desk")

        # Enable high-DPI support on Windows
        try:
            from ctypes import windll

            windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass

        self.root.geometry("1120x700")
        self.root.minsize(980, 620)

        self.palette = {
            "bg": "#f5efe6",
            "panel": "#0f1f2f",
            "panel_soft": "#17314a",
            "surface": "#fffdf9",
            "surface_alt": "#f3e4d0",
            "text": "#1f1a17",
            "muted": "#6a5b51",
            "accent": "#ff7b4a",
            "accent_hover": "#e86636",
            "ok": "#1f8d5f",
            "warn": "#b36b00",
        }

        self.root.configure(bg=self.palette["bg"])

        self.config_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "config", "config.toml")
        )
        self.config = load_config(self.config_path)

        self.controller = None
        self.target_path = tk.StringVar(value=self._initial_target_directory())

        watcher_cfg = self.config.get("watcher", {})
        remote_cfg = self.config.get("remote", {})

        self.debounce_var = tk.StringVar(
            value=str(watcher_cfg.get("debounce_ms", 2000))
        )
        self.max_size_var = tk.StringVar(
            value=str(watcher_cfg.get("max_file_size_mb", 50))
        )
        self.push_count_var = tk.StringVar(
            value=str(remote_cfg.get("push_interval_commits", 10))
        )
        self.push_mins_var = tk.StringVar(
            value=str(remote_cfg.get("push_interval_minutes", 30))
        )
        self.remote_enabled_var = tk.BooleanVar(value=remote_cfg.get("enabled", False))
        self.remote_url_var = tk.StringVar(value=remote_cfg.get("remote_url", ""))

        self.status_text = tk.StringVar(value="Idle - no folder being watched")
        self.branch_text = tk.StringVar(value="-")
        self.commit_count_text = tk.StringVar(value="0")
        self.remote_text = tk.StringVar(value="No remote")

        self.pages = {}
        self.nav_buttons = {}

        self._setup_style()
        self._create_layout()
        self._refresh_repository_stats()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _initial_target_directory(self):
        watcher_cfg = self.config.get("watcher", {})
        target = watcher_cfg.get("target_directory", ".")
        if target == ".":
            return os.getcwd()
        return os.path.abspath(target)

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Main.TFrame", background=self.palette["bg"])
        style.configure("Surface.TFrame", background=self.palette["surface"])
        style.configure("SurfaceAlt.TFrame", background=self.palette["surface_alt"])

        style.configure(
            "Primary.TButton",
            background=self.palette["accent"],
            foreground="white",
            padding=(14, 10),
            font=("Bahnschrift", 10, "bold"),
            borderwidth=0,
        )
        style.map(
            "Primary.TButton",
            background=[("active", self.palette["accent_hover"])],
            foreground=[("disabled", "#f2d9cf")],
        )

        style.configure(
            "Secondary.TButton",
            background=self.palette["panel_soft"],
            foreground="white",
            padding=(12, 9),
            font=("Bahnschrift", 10),
            borderwidth=0,
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#214564")],
            foreground=[("disabled", "#9bb0c0")],
        )

        style.configure(
            "History.Treeview",
            background=self.palette["surface"],
            fieldbackground=self.palette["surface"],
            foreground=self.palette["text"],
            rowheight=30,
            font=("Consolas", 10),
        )
        style.configure(
            "History.Treeview.Heading",
            background=self.palette["panel_soft"],
            foreground="white",
            font=("Bahnschrift", 10, "bold"),
            relief="flat",
        )
        style.map(
            "History.Treeview",
            background=[("selected", "#f6c9b8")],
            foreground=[("selected", self.palette["text"])],
        )

    def _create_layout(self):
        root_frame = ttk.Frame(self.root, style="Main.TFrame")
        root_frame.pack(fill="both", expand=True)

        left_panel = tk.Frame(root_frame, bg=self.palette["panel"], width=250)
        left_panel.pack(side="left", fill="y")
        left_panel.pack_propagate(False)

        content = tk.Frame(root_frame, bg=self.palette["bg"])
        content.pack(side="right", fill="both", expand=True)

        self._build_left_panel(left_panel)
        self._build_content(content)

    def _build_left_panel(self, panel):
        brand = tk.Frame(panel, bg=self.palette["panel"])
        brand.pack(fill="x", padx=18, pady=(24, 20))

        dot = tk.Canvas(
            brand, width=22, height=22, highlightthickness=0, bg=self.palette["panel"]
        )
        dot.create_oval(2, 2, 20, 20, fill=self.palette["accent"], outline="")
        dot.pack(side="left")

        tk.Label(
            brand,
            text="BackTrack",
            bg=self.palette["panel"],
            fg="white",
            font=("Bahnschrift", 18, "bold"),
        ).pack(side="left", padx=10)

        tk.Label(
            panel,
            text="small Git backup desk",
            bg=self.palette["panel"],
            fg="#a8bfd3",
            font=("Bahnschrift", 11),
        ).pack(anchor="w", padx=22)

        nav = tk.Frame(panel, bg=self.palette["panel"])
        nav.pack(fill="x", padx=14, pady=26)

        self._create_nav_button(nav, "Dashboard", "dashboard")
        self._create_nav_button(nav, "History", "history")
        self._create_nav_button(nav, "Settings", "settings")

        quick = tk.Frame(panel, bg=self.palette["panel_soft"], padx=12, pady=12)
        quick.pack(side="bottom", fill="x", padx=14, pady=16)

        tk.Label(
            quick,
            text="Current service state",
            bg=self.palette["panel_soft"],
            fg="#cfd9e2",
            font=("Bahnschrift", 9),
        ).pack(anchor="w")

        self.status_badge = tk.Label(
            quick,
            text="STOPPED",
            bg="#7f8b96",
            fg="white",
            font=("Bahnschrift", 10, "bold"),
            padx=8,
            pady=4,
        )
        self.status_badge.pack(anchor="w", pady=(8, 0))

    def _create_nav_button(self, parent, label, page_key):
        btn = tk.Button(
            parent,
            text=label,
            anchor="w",
            relief="flat",
            bd=0,
            padx=14,
            pady=10,
            bg=self.palette["panel"],
            fg="#d5e2ed",
            activebackground=self.palette["panel_soft"],
            activeforeground="white",
            font=("Bahnschrift", 12),
            command=lambda: self._show_page(page_key),
        )
        btn.pack(fill="x", pady=4)
        self.nav_buttons[page_key] = btn

    def _build_content(self, content):
        hero = tk.Frame(content, bg=self.palette["surface_alt"], height=115)
        hero.pack(fill="x", padx=22, pady=(22, 12))
        hero.pack_propagate(False)

        tk.Label(
            hero,
            text="Git backups, kept in one place",
            bg=self.palette["surface_alt"],
            fg=self.palette["text"],
            font=("Bahnschrift", 24, "bold"),
        ).pack(anchor="w", padx=18, pady=(16, 0))

        tk.Label(
            hero,
            textvariable=self.status_text,
            bg=self.palette["surface_alt"],
            fg=self.palette["muted"],
            font=("Bahnschrift", 11),
        ).pack(anchor="w", padx=20)

        page_host = tk.Frame(content, bg=self.palette["bg"])
        page_host.pack(fill="both", expand=True, padx=22, pady=(0, 22))

        self.pages["dashboard"] = self._build_dashboard_page(page_host)
        self.pages["history"] = self._build_history_page(page_host)
        self.pages["settings"] = self._build_settings_page(page_host)

        self._show_page("dashboard")

    def _build_dashboard_page(self, parent):
        page = tk.Frame(parent, bg=self.palette["bg"])
        page.place(relx=0, rely=0, relwidth=1, relheight=1)

        folder_card = tk.Frame(
            page,
            bg=self.palette["surface"],
            highlightbackground="#e2d5c8",
            highlightthickness=1,
        )
        folder_card.pack(fill="x", pady=(0, 12))

        tk.Label(
            folder_card,
            text="Project folder",
            bg=self.palette["surface"],
            fg=self.palette["text"],
            font=("Bahnschrift", 12, "bold"),
        ).pack(anchor="w", padx=14, pady=(12, 6))

        row = tk.Frame(folder_card, bg=self.palette["surface"])
        row.pack(fill="x", padx=14, pady=(0, 12))

        tk.Entry(
            row,
            textvariable=self.target_path,
            relief="flat",
            bg="#fff7ef",
            fg=self.palette["text"],
            font=("Consolas", 10),
            insertbackground=self.palette["text"],
        ).pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=7)

        ttk.Button(
            row, text="Browse", style="Secondary.TButton", command=self._browse_folder
        ).pack(side="left")

        controls = tk.Frame(page, bg=self.palette["bg"])
        controls.pack(fill="x", pady=(0, 12))

        self.start_btn = ttk.Button(
            controls,
            text="Start watching",
            style="Primary.TButton",
            command=self._toggle_service,
        )
        self.start_btn.pack(side="left")

        ttk.Button(
            controls,
            text="Refresh History",
            style="Secondary.TButton",
            command=self._refresh_history,
        ).pack(side="left", padx=10)

        ttk.Button(
            controls,
            text="Update stats",
            style="Secondary.TButton",
            command=self._refresh_repository_stats,
        ).pack(side="left")

        metric_row = tk.Frame(page, bg=self.palette["bg"])
        metric_row.pack(fill="x", pady=(0, 12))

        self._metric_card(metric_row, "Branch", self.branch_text).pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        self._metric_card(metric_row, "Commits", self.commit_count_text).pack(
            side="left", fill="x", expand=True, padx=4
        )
        self._metric_card(metric_row, "Remote", self.remote_text).pack(
            side="left", fill="x", expand=True, padx=(8, 0)
        )

        log_card = tk.Frame(
            page,
            bg=self.palette["surface"],
            highlightbackground="#e2d5c8",
            highlightthickness=1,
        )
        log_card.pack(fill="both", expand=True)

        tk.Label(
            log_card,
            text="Recent activity",
            bg=self.palette["surface"],
            fg=self.palette["text"],
            font=("Bahnschrift", 12, "bold"),
        ).pack(anchor="w", padx=14, pady=(12, 6))

        self.log_text = tk.Text(
            log_card,
            state="disabled",
            bg="#161a1e",
            fg="#d6e3ec",
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            padx=10,
            pady=10,
        )
        self.log_text.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        return page

    def _metric_card(self, parent, title, variable):
        card = tk.Frame(
            parent,
            bg=self.palette["surface"],
            highlightbackground="#e2d5c8",
            highlightthickness=1,
        )

        tk.Label(
            card,
            text=title,
            bg=self.palette["surface"],
            fg=self.palette["muted"],
            font=("Bahnschrift", 10),
        ).pack(anchor="w", padx=12, pady=(9, 0))
        tk.Label(
            card,
            textvariable=variable,
            bg=self.palette["surface"],
            fg=self.palette["text"],
            font=("Bahnschrift", 14, "bold"),
        ).pack(anchor="w", padx=12, pady=(0, 10))
        return card

    def _build_history_page(self, parent):
        page = tk.Frame(parent, bg=self.palette["bg"])
        page.place(relx=0, rely=0, relwidth=1, relheight=1)

        card = tk.Frame(
            page,
            bg=self.palette["surface"],
            highlightbackground="#e2d5c8",
            highlightthickness=1,
        )
        card.pack(fill="both", expand=True)

        tk.Label(
            card,
            text="Commit history",
            bg=self.palette["surface"],
            fg=self.palette["text"],
            font=("Bahnschrift", 13, "bold"),
        ).pack(anchor="w", padx=14, pady=(12, 8))

        tree_wrap = tk.Frame(card, bg=self.palette["surface"])
        tree_wrap.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        columns = ("hash", "message", "time")
        self.tree = ttk.Treeview(
            tree_wrap, columns=columns, show="headings", style="History.Treeview"
        )
        self.tree.heading("hash", text="Hash")
        self.tree.heading("message", text="Commit Message")
        self.tree.heading("time", text="Timestamp")

        self.tree.column("hash", width=90, anchor="center")
        self.tree.column("message", width=540, anchor="w")
        self.tree.column("time", width=190, anchor="center")

        scroll = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        actions = tk.Frame(card, bg=self.palette["surface"])
        actions.pack(fill="x", padx=14, pady=(0, 12))

        ttk.Button(
            actions,
            text="Refresh history",
            style="Secondary.TButton",
            command=self._refresh_history,
        ).pack(side="left")
        ttk.Button(
            actions,
            text="Roll back selected",
            style="Primary.TButton",
            command=self._restore_selected,
        ).pack(side="right")

        return page

    def _build_settings_page(self, parent):
        page = tk.Frame(parent, bg=self.palette["bg"])
        page.place(relx=0, rely=0, relwidth=1, relheight=1)

        card = tk.Frame(
            page,
            bg=self.palette["surface"],
            highlightbackground="#e2d5c8",
            highlightthickness=1,
        )
        card.pack(fill="both", expand=True)

        tk.Label(
            card,
            text="Backup settings",
            bg=self.palette["surface"],
            fg=self.palette["text"],
            font=("Bahnschrift", 13, "bold"),
        ).pack(anchor="w", padx=16, pady=(12, 8))

        grid = tk.Frame(card, bg=self.palette["surface"])
        grid.pack(fill="x", padx=16, pady=(0, 12))

        fields = [
            ("Debounce (ms)", self.debounce_var),
            ("Max File Size (MB)", self.max_size_var),
            ("Push Every N Commits", self.push_count_var),
            ("Push Every N Minutes", self.push_mins_var),
        ]

        for idx, (label, var) in enumerate(fields):
            tk.Label(
                grid,
                text=label,
                bg=self.palette["surface"],
                fg=self.palette["text"],
                font=("Bahnschrift", 10),
            ).grid(row=idx, column=0, sticky="w", pady=7)
            tk.Entry(
                grid,
                textvariable=var,
                relief="flat",
                bg="#fff7ef",
                fg=self.palette["text"],
                font=("Consolas", 10),
                insertbackground=self.palette["text"],
                width=16,
            ).grid(row=idx, column=1, sticky="w", padx=14, pady=7, ipady=5)

        tk.Frame(grid, bg="#e2d5c8", height=1).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=10
        )

        tk.Checkbutton(
            grid,
            text="Enable remote push",
            variable=self.remote_enabled_var,
            bg=self.palette["surface"],
            fg=self.palette["text"],
            activebackground=self.palette["surface"],
            font=("Bahnschrift", 10),
            selectcolor=self.palette["surface"],
        ).grid(row=6, column=0, sticky="w", pady=7)

        tk.Label(
            grid,
            text="Remote URL",
            bg=self.palette["surface"],
            fg=self.palette["text"],
            font=("Bahnschrift", 10),
        ).grid(row=7, column=0, sticky="w", pady=7)
        tk.Entry(
            grid,
            textvariable=self.remote_url_var,
            relief="flat",
            bg="#fff7ef",
            fg=self.palette["text"],
            font=("Consolas", 10),
            insertbackground=self.palette["text"],
            width=45,
        ).grid(row=7, column=1, sticky="w", padx=14, pady=7, ipady=5)

        buttons = tk.Frame(card, bg=self.palette["surface"])
        buttons.pack(fill="x", padx=16, pady=(0, 14))

        ttk.Button(
            buttons,
            text="Save settings",
            style="Primary.TButton",
            command=self._save_settings,
        ).pack(side="right")

        return page

    def _show_page(self, page_key):
        self.pages[page_key].tkraise()
        for key, btn in self.nav_buttons.items():
            if key == page_key:
                btn.config(bg=self.palette["panel_soft"], fg="white")
            else:
                btn.config(bg=self.palette["panel"], fg="#d5e2ed")

    def _browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.target_path.get())
        if folder:
            self.target_path.set(folder)
            self._refresh_history()
            self._refresh_repository_stats()
            self._log_gui(f"Target folder changed to {folder}")

    def _toggle_service(self):
        if self.controller and self.controller._running:
            self.controller.stop()
            self._set_stopped_state()
            self._log_gui("Backup service stopped.")
            return

        target = self.target_path.get().strip()
        if not target:
            messagebox.showerror("Invalid Target", "Please select a target directory.")
            return
        if not os.path.isdir(target):
            messagebox.showerror("Invalid Target", "Target directory does not exist.")
            return

        try:
            self.controller = BackupController(target, self.config)
            self.controller.start()
            self.start_btn.config(text="Stop watching")
            self.status_text.set(f"Watching {target}")
            self.status_badge.config(text="RUNNING", bg=self.palette["ok"])
            self._log_gui(f"Watching started on {target}")
            self._refresh_history()
            self._refresh_repository_stats()
        except Exception as exc:
            messagebox.showerror("Service Error", f"Failed to start service: {exc}")

    def _set_stopped_state(self):
        self.start_btn.config(text="Start watching")
        self.status_text.set("Idle - no folder being watched")
        self.status_badge.config(text="IDLE", bg="#7f8b96")

    def _log_gui(self, message):
        self.log_text.config(state="normal")
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{stamp}] {message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _refresh_repository_stats(self):
        try:
            repo = git.Repo(self.target_path.get())
            self.branch_text.set(repo.active_branch.name)
            self.commit_count_text.set(str(sum(1 for _ in repo.iter_commits())))
            self.remote_text.set(
                "origin"
                if any(r.name == "origin" for r in repo.remotes)
                else "No remote"
            )
            repo.close()
        except Exception:
            self.branch_text.set("-")
            self.commit_count_text.set("0")
            self.remote_text.set("No repo")

    def _refresh_history(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            repo = git.Repo(self.target_path.get())
            for commit in repo.iter_commits(max_count=80):
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        commit.hexsha[:7],
                        commit.summary,
                        datetime.fromtimestamp(commit.committed_date).strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                    ),
                )
            repo.close()
        except Exception:
            pass

    def _restore_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Choose a backup entry to restore.")
            return

        item = self.tree.item(selected[0])
        commit_hash = item["values"][0]

        confirm = messagebox.askyesno(
            "Confirm Restore",
            f"This checks out commit {commit_hash}. Continue?",
        )
        if not confirm:
            return

        try:
            repo = git.Repo(self.target_path.get())
            repo.git.checkout(commit_hash)
            repo.close()
            self._log_gui(f"Repository restored to {commit_hash}")
            messagebox.showinfo(
                "Restore Complete", f"Checked out commit {commit_hash}."
            )
            self._refresh_repository_stats()
        except Exception as exc:
            messagebox.showerror("Restore Error", str(exc))

    def _save_settings(self):
        try:
            debounce = int(self.debounce_var.get())
            max_file_size = int(self.max_size_var.get())
            push_commits = int(self.push_count_var.get())
            push_minutes = int(self.push_mins_var.get())

            if (
                debounce <= 0
                or max_file_size <= 0
                or push_commits <= 0
                or push_minutes <= 0
            ):
                raise ValueError("Numeric settings must be greater than zero.")

            watcher_cfg = self.config.setdefault("watcher", {})
            git_cfg = self.config.setdefault("git", {})
            remote_cfg = self.config.setdefault("remote", {})

            watcher_cfg["target_directory"] = self.target_path.get()
            watcher_cfg["debounce_ms"] = debounce
            watcher_cfg.setdefault("recursive", True)
            watcher_cfg.setdefault("exclude_extensions", [".swp", ".tmp", "~", ".git"])
            watcher_cfg["max_file_size_mb"] = max_file_size

            git_cfg.setdefault(
                "commit_message_template",
                "[BACKUP] {event_type}: {filename} @ {timestamp}",
            )
            git_cfg.setdefault("branch", "main")

            remote_cfg["enabled"] = self.remote_enabled_var.get()
            remote_cfg["remote_url"] = self.remote_url_var.get().strip()
            remote_cfg["push_interval_commits"] = push_commits
            remote_cfg["push_interval_minutes"] = push_minutes

            self._write_toml_config(self.config)
            self._log_gui("Configuration saved.")
            messagebox.showinfo("Saved", "Configuration updated successfully.")
        except ValueError as exc:
            messagebox.showerror("Invalid Settings", str(exc))
        except Exception as exc:
            messagebox.showerror("Save Error", f"Could not save configuration: {exc}")

    def _write_toml_config(self, data):
        sections = ["watcher", "git", "remote"]
        lines = []

        for section in sections:
            section_data = data.get(section, {})
            lines.append(f"[{section}]")
            for key, value in section_data.items():
                lines.append(f"{key} = {self._toml_value(value)}")
            lines.append("")

        with open(self.config_path, "w", encoding="utf-8") as cfg_file:
            cfg_file.write("\n".join(lines).strip() + "\n")

    def _toml_value(self, value):
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return str(value)
        if isinstance(value, list):
            serialized = ", ".join(self._toml_value(item) for item in value)
            return f"[{serialized}]"
        text = str(value).replace("\\", "\\\\").replace('"', '\\"')
        return f'"{text}"'

    def _on_close(self):
        if self.controller and self.controller._running:
            self.controller.stop()
        self.root.destroy()


def run_gui():
    # Enable high-DPI support on Windows before creating window
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

    root = tk.Tk()
    BackupGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
