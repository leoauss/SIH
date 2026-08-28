"""Primary ForensiDrive window."""

import tkinter as tk

from core.system import APP_NAME, APP_VERSION
from modules.dashboard.dashboard import DashboardView
from modules.erasure.erasure import ErasureView
from modules.inspection.inspection import InspectionView
from modules.recovery.recovery import RecoveryView
from modules.file_eraser.file_eraser import FileEraserView
from modules.audit.audit_view import AuditView
from ui.navigation import Navigation
from ui.theme import Theme, apply


class AppWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("%s %s" % (APP_NAME, APP_VERSION))
        self.root.minsize(960, 640)
        apply(self.root)
        self._go_fullscreen()

        shell = tk.Frame(self.root, bg=Theme.BG)
        shell.pack(fill="both", expand=True)

        header = tk.Frame(shell, bg=Theme.SURFACE)
        header.pack(fill="x")
        tk.Label(header, text=APP_NAME, bg=Theme.SURFACE, fg=Theme.TEXT, font=(Theme.FONT, 18, "bold")).pack(side="left", padx=20, pady=14)
        tk.Label(header, text="Storage recovery and erasure", bg=Theme.SURFACE, fg=Theme.MUTED, font=(Theme.FONT, 12)).pack(side="left", padx=(0, 20))

        self._home_btn = tk.Button(
            header,
            text="Home",
            command=self.show_dashboard,
            bg=Theme.SURFACE_ALT,
            fg=Theme.TEXT,
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        )
        self._home_btn.pack(side="right", padx=20)

        body = tk.Frame(shell, bg=Theme.BG)
        body.pack(fill="both", expand=True, padx=24, pady=20)
        self.nav = Navigation(body)
        self.nav.register("dashboard", lambda parent: DashboardView(parent, self))
        self.nav.register("inspection", lambda parent, **kw: InspectionView(parent, self, **kw))
        self.nav.register("recovery", lambda parent, **kw: RecoveryView(parent, self, **kw))
        self.nav.register("erasure", lambda parent, **kw: ErasureView(parent, self, **kw))
        self.nav.register("file_eraser", lambda parent, **kw: FileEraserView(parent, self, **kw))
        self.nav.register("audit", lambda parent: AuditView(parent, self))
        self.show_dashboard()

        self.root.bind("<Escape>", self._maybe_exit_fullscreen)

    def _go_fullscreen(self) -> None:
        try:
            self.root.attributes("-fullscreen", True)
        except tk.TclError:
            try:
                self.root.state("zoomed")
            except tk.TclError:
                self.root.geometry("1200x800")

    def _maybe_exit_fullscreen(self, _event=None):
        try:
            current = bool(self.root.attributes("-fullscreen"))
            self.root.attributes("-fullscreen", not current)
        except tk.TclError:
            pass

    def show_dashboard(self):
        self.nav.show("dashboard")

    def show_inspection(self):
        self.nav.show("inspection")

    def show_recovery(self):
        self.nav.show("recovery")

    def show_erasure(self):
        self.nav.show("erasure")

    def show_file_eraser(self):
        self.nav.show("file_eraser")

    def show_audit(self):
        self.nav.show("audit")

    def show_system_info(self):
        from modules.dashboard.dashboard import SystemInfoView

        if self.nav._current is not None:
            self.nav._current.destroy()
        view = SystemInfoView(self.nav.container, self)
        view.pack(fill="both", expand=True)
        self.nav._current = view
        self.nav._name = "system"
