#!/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import subprocess
import curses
import signal
import sys
import functools
import threading
from typing import Any, Dict, List, Tuple, Union, Sequence, Optional


# =============================================================================
# PackageInstallerApp: A TUI package installer with i18n support.
# =============================================================================
class PackageInstallerApp:
    # Configuration: use emoji if available.
    USE_EMOJI: bool = True

    # Markers for category display.
    if USE_EMOJI:
        CATEGORY_MARKER_INSTALLED = "✅"  # All installed
        CATEGORY_MARKER_PARTIAL = "⚠️"  # Some installed
        CATEGORY_MARKER_AVAILABLE = "➕"  # None installed
        # Markers for package selection:
        PACKAGE_SELECTED = "☑️"
        PACKAGE_UNSELECTED = "⬜"
    else:
        CATEGORY_MARKER_INSTALLED = "[X]"
        CATEGORY_MARKER_PARTIAL = "[~]"
        CATEGORY_MARKER_AVAILABLE = "[+]"
        PACKAGE_SELECTED = "[*]"
        PACKAGE_UNSELECTED = "[ ]"

    # Buttons (plain text)
    DEFAULT_INSTALL_BUTTON = "Install"
    DEFAULT_BACK_BUTTON = "Back"

    # Layout constants.
    HEADER_ROW: int = 0
    INFO_ROW: int = 1
    MENU_START_ROW: int = 7

    # Default translations (i18n)
    DEFAULT_TRANSLATIONS: Dict[str, str] = {
        "header": "Package Installer",
        "footer": "Scarlett Samantha Verheul <scarlett.verheul@gmail.com> https://scarlettbytes.nl",
        "menu_instructions": (
            "[↑/↓: Navigate, →/Enter: Select, ESC/←/B: Back, Space: Toggle selection, i: Install selected, I: Info, R: Uninstall, L: List, Q: Quit]"
        ),
        "select_distro": "Select a Distribution:",
        "select_method": "Select an Install Method:",
        "select_category": "Select Categories (→ to expand, Space to toggle selection):",
        "select_package": "Select a package (Enter toggles selection, R to uninstall)",
        "installation_log": "Installation Log:",
        "uninstallation_log": "Uninstallation Log:",
        "no_packages_install": "No packages to install in this category.",
        "no_packages_uninstall": "No packages to uninstall in this category.",
        "install_complete": "Installation Complete! Press R to reboot, any other key to exit.",
        "category_install_complete": "Category installation complete! Press any key to return.",
        "category_uninstall_complete": "Category uninstallation complete! Press any key to return.",
        "install_button": "Install",
        "back_button": "Back",
        "message_duration": "1500",  # milliseconds
    }

    @property
    def key_escape(self) -> int:
        return 27  # ESC

    def __init__(
        self,
        package_file: str = "packages.json",
        translations: Optional[Dict[str, str]] = None,
    ) -> None:
        with open(package_file, "r") as f:
            self.package_data: Dict[str, Any] = json.load(f)
        self.selected_distro: str = ""
        self.selected_method: str = ""
        self.selected_packages: set[str] = (
            set()
        )  # holds package names selected for installation.
        self.current_category: str = ""
        self.translations: Dict[str, str] = (
            translations if translations is not None else self.DEFAULT_TRANSLATIONS
        )
        self.last_selected_count: int = 0  # For animating package count

        self.menu_positions: Dict[str, int] = {
            "distros": 0,
            "methods": 0,
            "packages": 0,
            "category": 0,
        }
        # start warming up the install-status cache in the background
        self.cache_loading: bool = False
        self._async_preload_install_status()

    def get_package_data(
        self, os: str = "Ubuntu", method: str = "Raw", package: Optional[str] = None
    ) -> Dict[str, Any]:
        package_data = self.package_data.get(os, {}).get(method, {})
        try:
            if isinstance(package_data, dict):
                packages: List[Dict[str, Any]] = package_data.get("Manual Install", [])
                for pkg in packages:
                    if isinstance(pkg, dict) and pkg.get("name") == package:
                        return pkg
            return {}
        except KeyError:
            return {}

    def _async_preload_install_status(self) -> None:
        """
        Launch a daemon thread that walks every (method,package) pair
        and calls is_package_installed so the lru_cache is populated
        before the UI needs it.
        Stores the thread as self._preload_thread.
        """

        def _worker() -> None:
            # build flat list of (method, pkg_name)
            tasks: list[tuple[str, str]] = []
            for distro, methods in self.package_data.items():
                for method, categories in methods.items():
                    for category in categories:
                        _, pkg_list = self.get_category_data(distro, method, category)
                        for pkg in pkg_list:
                            name = self.get_pkg_name(pkg)
                            tasks.append((method, name))

            # dispatch on a small thread‐pool
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(self.is_package_installed, method, name)
                    for method, name in tasks
                ]
                # wait for all to complete (results go into the cache)
                for _ in as_completed(futures):
                    pass

        # start the daemon thread, keep a reference
        self._preload_thread = threading.Thread(target=_worker, daemon=True)
        self._preload_thread.start()

    # i18n property getters.
    @property
    def header_text(self) -> str:
        return self.translations.get("header", self.DEFAULT_TRANSLATIONS["header"])

    @property
    def footer_text(self) -> str:
        return self.translations.get("footer", self.DEFAULT_TRANSLATIONS["footer"])

    @property
    def menu_instructions(self) -> str:
        return self.translations.get(
            "menu_instructions", self.DEFAULT_TRANSLATIONS["menu_instructions"]
        )

    @property
    def select_distro_text(self) -> str:
        return self.translations.get(
            "select_distro", self.DEFAULT_TRANSLATIONS["select_distro"]
        )

    @property
    def select_method_text(self) -> str:
        return self.translations.get(
            "select_method", self.DEFAULT_TRANSLATIONS["select_method"]
        )

    @property
    def select_category_text(self) -> str:
        return self.translations.get(
            "select_category", self.DEFAULT_TRANSLATIONS["select_category"]
        )

    @property
    def select_package_text(self) -> str:
        return self.translations.get(
            "select_package", self.DEFAULT_TRANSLATIONS["select_package"]
        )

    @property
    def installation_log_text(self) -> str:
        return self.translations.get(
            "installation_log", self.DEFAULT_TRANSLATIONS["installation_log"]
        )

    @property
    def uninstallation_log_text(self) -> str:
        return self.translations.get(
            "uninstallation_log", self.DEFAULT_TRANSLATIONS["uninstallation_log"]
        )

    @property
    def no_packages_install_text(self) -> str:
        return self.translations.get(
            "no_packages_install", self.DEFAULT_TRANSLATIONS["no_packages_install"]
        )

    @property
    def no_packages_uninstall_text(self) -> str:
        return self.translations.get(
            "no_packages_uninstall", self.DEFAULT_TRANSLATIONS["no_packages_uninstall"]
        )

    @property
    def install_complete_text(self) -> str:
        return self.translations.get(
            "install_complete", self.DEFAULT_TRANSLATIONS["install_complete"]
        )

    @property
    def category_install_complete_text(self) -> str:
        return self.translations.get(
            "category_install_complete",
            self.DEFAULT_TRANSLATIONS["category_install_complete"],
        )

    @property
    def category_uninstall_complete_text(self) -> str:
        return self.translations.get(
            "category_uninstall_complete",
            self.DEFAULT_TRANSLATIONS["category_uninstall_complete"],
        )

    @property
    def message_duration(self) -> int:
        try:
            return int(
                self.translations.get(
                    "message_duration", self.DEFAULT_TRANSLATIONS["message_duration"]
                )
            )
        except ValueError:
            return 1500

    @property
    def install_button_text(self) -> str:
        return self.translations.get(
            "install_button", self.DEFAULT_TRANSLATIONS["install_button"]
        )

    @property
    def back_button_text(self) -> str:
        return self.translations.get(
            "back_button", self.DEFAULT_TRANSLATIONS["back_button"]
        )

    # -------------------------------------------------------------------------
    # Helper functions for JSON structure.
    # -------------------------------------------------------------------------
    def get_category_data(
        self, distro: str, method: str, category: str
    ) -> Tuple[str, List[Any]]:
        data = self.package_data[distro][method][category]
        if isinstance(data, dict):
            return data.get("description", ""), data.get("packages", [])
        return "", data

    def get_pkg_name(self, pkg: Optional[Union[str, Dict[str, Any]]]) -> str:
        if pkg is None:
            return ""
        if isinstance(pkg, dict):
            return pkg.get("name", "")
        return pkg

    def get_package_display_text(
        self, pkg: Optional[Union[str, Dict[str, Any]]]
    ) -> str:
        name = self.get_pkg_name(pkg)
        if isinstance(pkg, dict):
            desc = pkg.get("description", "")
            if desc:
                return f"{name} - {desc}"
        return name

    def get_category_display_text(self, distro: str, method: str, category: str) -> str:
        description, packages = self.get_category_data(distro, method, category)
        total = len(packages)
        installed = sum(
            1
            for pkg in packages
            if self.is_package_installed(method, self.get_pkg_name(pkg))
        )
        if total > 0 and installed == total:
            marker = self.CATEGORY_MARKER_INSTALLED
        elif installed > 0:
            marker = self.CATEGORY_MARKER_PARTIAL
        else:
            marker = self.CATEGORY_MARKER_AVAILABLE
        base = f"{marker} {category} ({installed}/{total})"
        if description:
            return f"{base} - {description}"
        return base

    # -------------------------------------------------------------------------
    # Package status and command functions.
    # -------------------------------------------------------------------------
    @functools.lru_cache(maxsize=None)
    def is_package_installed(self, method: str, package: str) -> bool | int:
        if method == "APT":
            cmd: str = f"dpkg -s {package} > /dev/null 2>&1"
        elif method == "Snap":
            cmd = f"snap list {package} > /dev/null 2>&1"
        elif method == "Flatpak":
            cmd = f"flatpak info {package} > /dev/null 2>&1"
        elif method.lower() == "raw":
            if (
                _cmd := self.get_package_data(method=method, package=package).get(
                    "check_command", None
                )
            ) is None:
                cmd = f"which {package} > /dev/null 2>&1"
            else:
                cmd = _cmd + " > /dev/null 2>&1"
        else:
            return False
        result = subprocess.run(cmd, shell=True)
        return result.returncode == 0

    @staticmethod
    def install_package_cmd(command: str) -> None:
        subprocess.run(
            command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    @staticmethod
    def uninstall_package_cmd(command: str) -> None:
        subprocess.run(
            command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    def get_install_command(self, method: str, package: str) -> str:
        if method == "APT":
            return f"sudo apt install -y {package}"
        elif method == "Snap":
            return f"sudo snap install {package}"
        elif method == "Flatpak":
            return f"flatpak install -y {package}"
        elif method.lower() == "raw":
            return self._get_raw_install_command(method, package)
        return ""

    def _get_raw_install_command(self, method: str, package: str) -> str:
        """
        Downloads the installer into a temp dir, runs it (rewriting {file} or filename
        if present), moves the downloaded file into /usr/local/bin/<binname>, then cleans up.
        """
        data = self.get_package_data(method=method, package=package)
        if not isinstance(data, Dict):
            return ""

        install_cmd = data.get("install_command", "").strip()
        url = data.get("url", "").strip()
        if not install_cmd or not url:
            return ""

        # derive paths
        filename = url.rsplit("/", 1)[-1]  # e.g. "phpcbf.phar"
        file_path = f"$tmpdir/{filename}"  # "$tmpdir/phpcbf.phar"
        bin_name = filename.rsplit(".", 1)[0]  # "phpcbf"
        dest_path = f"/usr/local/bin/{bin_name}"

        # pick runner (php for .phar, bash otherwise)
        runner = "php" if filename.endswith(".phar") else "bash"

        # download → run → move → cleanup
        base = f'tmpdir=$(mktemp -d) && curl -s {url} -o "{file_path}" && '

        # rewrite install invocation
        if "{file}" in install_cmd:
            cmd = install_cmd.replace("{file}", file_path)
        elif filename in install_cmd:
            cmd = install_cmd.replace(filename, file_path)
        else:
            cmd = f'{runner} "{file_path}" -- {install_cmd}'

        # full chain: download, run, move, cleanup
        return (
            base + cmd + f' && mv "{file_path}" "{dest_path}"' + ' && rm -rf "$tmpdir"'
        )

    @staticmethod
    def get_uninstall_command(method: str, package: str) -> str:
        if method == "APT":
            return f"sudo apt remove -y {package}"
        elif method == "Snap":
            return f"sudo snap remove {package}"
        elif method == "Flatpak":
            return f"flatpak uninstall -y {package}"
        return ""

    # -------------------------------------------------------------------------
    # Run a command while showing a Braille spinner animation.
    # -------------------------------------------------------------------------
    def run_command_with_spinner(
        self, stdscr: curses.window, cmd: str, row: int, col: int
    ) -> None:
        """
        Run a shell command asynchronously and display a Braille spinner at (row, col)
        until the command finishes.
        """
        spinner: List[str] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        proc = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        spinner_index: int = 0
        while proc.poll() is None:
            stdscr.addstr(row, col, spinner[spinner_index % len(spinner)])
            stdscr.refresh()
            spinner_index += 1
            curses.napms(100)
        # Clear spinner when done.
        stdscr.addstr(row, col, " ")
        stdscr.refresh()

    # -------------------------------------------------------------------------
    # UI utility functions.
    # -------------------------------------------------------------------------
    def draw_progress_bar(
        self,
        stdscr: curses.window,
        current: int,
        total: int,
        row: int,
        col: int,
        bar_width: int,
    ) -> None:
        fraction: float = current / total
        filled_length: int = int(round(bar_width * fraction))
        bar: str = "#" * filled_length + "-" * (bar_width - filled_length)
        progress_percent: int = int(fraction * 100)
        stdscr.addstr(row, col, f"[{bar}] {progress_percent}%")

    def show_temp_message(
        self, stdscr: curses.window, message: str, duration: Optional[int] = None
    ) -> None:
        height, _ = stdscr.getmaxyx()
        dur = duration if duration is not None else self.message_duration
        stdscr.addstr(height - 2, 2, message, curses.A_BOLD)
        stdscr.refresh()
        curses.napms(dur)

    def popup_message(self, stdscr: curses.window, message: str) -> None:
        """Display a popup window with the given message and an OK button."""
        height, width = stdscr.getmaxyx()
        win_height = 5
        win_width = min(len(message) + 10, width - 4)
        start_y = (height - win_height) // 2
        start_x = (width - win_width) // 2
        win = curses.newwin(win_height, win_width, start_y, start_x)
        win.box()
        msg_x = (win_width - len(message)) // 2
        win.addstr(2, msg_x, message)
        ok_text = "[ OK ]"
        win.addstr(win_height - 2, win_width - len(ok_text) - 2, ok_text, curses.A_BOLD)
        win.refresh()
        win.getch()
        win.clear()
        stdscr.refresh()

    def confirm_action(self, stdscr: curses.window, message: str) -> bool:
        """Display a confirmation popup with 'Yes/No' and return True if confirmed."""
        height, width = stdscr.getmaxyx()
        win_height = 5
        win_width = min(len(message) + 20, width - 4)
        start_y = (height - win_height) // 2
        start_x = (width - win_width) // 2
        win = curses.newwin(win_height, win_width, start_y, start_x)
        win.box()
        msg_x = (win_width - len(message)) // 2
        win.addstr(2, msg_x, message)
        win.addstr(win_height - 2, win_width - 20, "[Y]es / [N]o", curses.A_BOLD)
        win.refresh()
        ch = win.getch()
        win.clear()
        stdscr.refresh()
        return ch in (ord("y"), ord("Y"))

    def nice_exit_popup(self, stdscr: curses.window) -> None:
        """Display a nice exit popup before leaving the application."""
        height, width = stdscr.getmaxyx()
        win_height = 5
        exit_message = "Thank you for using Package Installer. Goodbye!"
        win_width = min(len(exit_message) + 10, width - 4)
        start_y = (height - win_height) // 2
        start_x = (width - win_width) // 2
        win = curses.newwin(win_height, win_width, start_y, start_x)
        win.box()
        msg_x = (win_width - len(exit_message)) // 2
        win.addstr(2, msg_x, exit_message)
        ok_text = "[ OK ]"
        win.addstr(win_height - 2, win_width - len(ok_text) - 2, ok_text, curses.A_BOLD)
        win.refresh()
        win.getch()
        win.clear()
        stdscr.refresh()

    def list_installed_packages(self, stdscr: curses.window) -> None:
        """Display a popup listing all installed packages for the current backend."""
        if not self.selected_distro or not self.selected_method:
            self.popup_message(
                stdscr, "Please select a distribution and backend first."
            )
            return
        installed_list = []
        for category in self.package_data[self.selected_distro][self.selected_method]:
            _, packages = self.get_category_data(
                self.selected_distro, self.selected_method, category
            )
            for pkg in packages:
                pkg_name = self.get_pkg_name(pkg)
                if self.is_package_installed(self.selected_method, pkg_name):
                    installed_list.append(f"{pkg_name} ({category})")
        if not installed_list:
            self.popup_message(stdscr, "No packages installed from current backend.")
            return
        height, width = stdscr.getmaxyx()
        win_height = min(max(10, len(installed_list) + 4), height - 4)
        win_width = min(max(max(len(s) for s in installed_list) + 4, 40), width - 4)
        start_y = (height - win_height) // 2
        start_x = (width - win_width) // 2
        win = curses.newwin(win_height, win_width, start_y, start_x)
        win.box()
        win.addstr(1, 2, "Installed Packages:", curses.A_BOLD)
        for i, line in enumerate(installed_list[: win_height - 3]):
            try:
                win.addstr(2 + i, 2, line[: win_width - 4])
            except curses.error:
                pass
        win.addstr(win_height - 2, win_width - 10, "[ OK ]", curses.A_BOLD)
        win.refresh()
        win.getch()
        win.clear()
        stdscr.refresh()

    def show_package_info(
        self, stdscr: curses.window, package: str, method: str
    ) -> None:
        if method == "APT":
            cmd = f"dpkg -s {package}"
        elif method == "Snap":
            cmd = f"snap info {package}"
        elif method == "Flatpak":
            cmd = f"flatpak info {package}"
        else:
            return
        result = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        info = result.stdout.decode("utf-8", errors="replace") or result.stderr.decode(
            "utf-8", errors="replace"
        )
        stdscr.clear()
        stdscr.addstr(0, 0, f"Package Info for {package}:", curses.A_BOLD)
        lines = info.splitlines()
        max_y, max_x = stdscr.getmaxyx()
        for i, line in enumerate(lines[: max_y - 2]):
            try:
                stdscr.addstr(1 + i, 0, line[: max_x - 1])
            except curses.error:
                pass
        stdscr.addstr(max_y - 1, 0, "Press any key to return...")
        stdscr.refresh()
        stdscr.getch()

    def uninstall_individual_package(self, stdscr: curses.window, package: str) -> None:
        if self.is_package_installed(self.selected_method, package):
            if self.confirm_action(stdscr, f"Uninstall {package}?"):
                cmd = self.get_uninstall_command(self.selected_method, package)
                if cmd:
                    self.uninstall_package_cmd(cmd)
                    PackageInstallerApp.is_package_installed.cache_clear()
                self.popup_message(stdscr, f"{package} uninstalled.")
            else:
                self.popup_message(stdscr, "Uninstall cancelled.")
        else:
            self.popup_message(stdscr, f"{package} is not installed.")

    # -------------------------------------------------------------------------
    # Category-level install/uninstall methods.
    # -------------------------------------------------------------------------
    def install_category_packages(self, stdscr: curses.window) -> None:
        stdscr.clear()
        stdscr.addstr(
            1, 2, f"{self.install_button_text} {self.current_category}", curses.A_BOLD
        )
        stdscr.addstr(
            2,
            2,
            f"{self.installation_log_text} (Using backend: {self.selected_method})",
            curses.A_BOLD,
        )
        stdscr.refresh()
        _, packages = self.get_category_data(
            self.selected_distro, self.selected_method, self.current_category
        )
        selected_in_category = [
            pkg for pkg in packages if self.get_pkg_name(pkg) in self.selected_packages
        ]
        if selected_in_category:
            to_install = selected_in_category
        else:
            to_install = [
                pkg
                for pkg in packages
                if not self.is_package_installed(
                    self.selected_method, self.get_pkg_name(pkg)
                )
            ]
        if not to_install:
            stdscr.addstr(3, 2, self.no_packages_install_text, curses.A_REVERSE)
            stdscr.refresh()
            stdscr.getch()
            return
        total = len(to_install)
        _, width = stdscr.getmaxyx()
        bar_width = max(10, width - 20)
        stdscr.refresh()
        for idx, pkg in enumerate(to_install, start=1):
            pkg_name = self.get_pkg_name(pkg)
            install_text = f"Installing: {pkg_name}"
            stdscr.addstr(3, 2, install_text, curses.A_BOLD)
            stdscr.clrtoeol()
            spinner_col = 2 + len(install_text) + 1
            self.draw_progress_bar(
                stdscr, idx, total, row=4, col=2, bar_width=bar_width
            )
            stdscr.refresh()
            log_row = 5 + idx
            if self.is_package_installed(self.selected_method, pkg_name):
                stdscr.addstr(
                    log_row,
                    2,
                    f"Already installed {self.CATEGORY_MARKER_INSTALLED}: {pkg_name}",
                    curses.color_pair(2) | curses.A_BOLD,
                )
            else:
                cmd = self.get_install_command(self.selected_method, pkg_name)

                if cmd:
                    self.run_command_with_spinner(stdscr, cmd, row=3, col=spinner_col)
                    PackageInstallerApp.is_package_installed.cache_clear()
                stdscr.addstr(
                    log_row,
                    2,
                    f"Installed {self.CATEGORY_MARKER_INSTALLED}: {pkg_name}",
                    curses.color_pair(3) | curses.A_BOLD,
                )
            stdscr.refresh()
        stdscr.addstr(
            7 + total, 2, self.category_install_complete_text, curses.A_REVERSE
        )
        stdscr.refresh()
        stdscr.getch()

    def uninstall_category_packages(self, stdscr: curses.window) -> None:
        stdscr.clear()
        stdscr.addstr(
            1, 2, f"{self.back_button_text} {self.current_category}", curses.A_BOLD
        )
        stdscr.refresh()
        _, packages = self.get_category_data(
            self.selected_distro, self.selected_method, self.current_category
        )
        selected_in_category = [
            pkg for pkg in packages if self.get_pkg_name(pkg) in self.selected_packages
        ]
        if selected_in_category:
            to_uninstall = selected_in_category
        else:
            to_uninstall = [
                pkg
                for pkg in packages
                if self.is_package_installed(
                    self.selected_method, self.get_pkg_name(pkg)
                )
            ]
        if not to_uninstall:
            stdscr.addstr(3, 2, self.no_packages_uninstall_text, curses.A_REVERSE)
            stdscr.refresh()
            stdscr.getch()
            return
        total = len(to_uninstall)
        _, width = stdscr.getmaxyx()
        bar_width = max(10, width - 20)
        stdscr.addstr(2, 2, self.uninstallation_log_text, curses.A_BOLD)
        stdscr.refresh()
        for idx, pkg in enumerate(to_uninstall, start=1):
            pkg_name = self.get_pkg_name(pkg)
            stdscr.addstr(3, 2, f"Uninstalling: {pkg_name}", curses.A_BOLD)
            stdscr.clrtoeol()
            self.draw_progress_bar(
                stdscr, idx, total, row=4, col=2, bar_width=bar_width
            )
            stdscr.refresh()
            log_row = 5 + idx
            if not self.is_package_installed(self.selected_method, pkg_name):
                stdscr.addstr(
                    log_row,
                    2,
                    f"Already uninstalled: {pkg_name}",
                    curses.color_pair(4) | curses.A_BOLD,
                )
            else:
                cmd = self.get_uninstall_command(self.selected_method, pkg_name)
                if cmd:
                    self.uninstall_package_cmd(cmd)
                    PackageInstallerApp.is_package_installed.cache_clear()
                stdscr.addstr(
                    log_row,
                    2,
                    f"Uninstalled: {pkg_name}",
                    curses.color_pair(3) | curses.A_BOLD,
                )
            stdscr.refresh()
        stdscr.addstr(
            7 + total, 2, self.category_uninstall_complete_text, curses.A_REVERSE
        )
        stdscr.refresh()
        stdscr.getch()

    def install_selected_packages(self, stdscr: curses.window) -> None:
        stdscr.clear()
        stdscr.addstr(1, 2, "Installing Selected Packages...", curses.A_BOLD)
        stdscr.refresh()
        if not self.selected_packages:
            stdscr.addstr(3, 2, "No packages selected!", curses.A_REVERSE)
            stdscr.refresh()
            stdscr.getch()
            return
        total = len(self.selected_packages)
        _, width = stdscr.getmaxyx()
        bar_width = max(10, width - 20)
        stdscr.addstr(
            2,
            2,
            f"{self.installation_log_text} (Using backend: {self.selected_method})",
            curses.A_BOLD,
        )
        stdscr.refresh()
        for idx, pkg in enumerate(self.selected_packages, start=1):
            install_text = f"Installing: {pkg}"
            stdscr.addstr(3, 2, install_text, curses.A_BOLD)
            stdscr.clrtoeol()
            spinner_col = 2 + len(install_text) + 1
            self.draw_progress_bar(
                stdscr, idx, total, row=4, col=2, bar_width=bar_width
            )
            stdscr.refresh()
            log_row = 5 + idx
            if self.is_package_installed(self.selected_method, pkg):
                stdscr.addstr(
                    log_row,
                    2,
                    f"Already installed {self.CATEGORY_MARKER_INSTALLED}: {pkg}",
                    curses.color_pair(2) | curses.A_BOLD,
                )
            else:
                cmd = self.get_install_command(self.selected_method, pkg)
                if cmd:
                    self.run_command_with_spinner(stdscr, cmd, row=3, col=spinner_col)
                    PackageInstallerApp.is_package_installed.cache_clear()
                stdscr.addstr(
                    log_row,
                    2,
                    f"Installed {self.CATEGORY_MARKER_INSTALLED}: {pkg}",
                    curses.color_pair(3) | curses.A_BOLD,
                )
            stdscr.refresh()
        stdscr.addstr(7 + total, 2, self.install_complete_text, curses.A_REVERSE)
        stdscr.refresh()
        ch = stdscr.getch()
        if ch == ord("R"):
            curses.endwin()
            print("Rebooting now...")
            subprocess.run("sudo reboot", shell=True)
        else:
            curses.endwin()

    def animate_selected_count(self, stdscr: curses.window, old: int, new: int) -> None:
        """
        Animate the 'Selected Packages' counter from old to new value.
        Flash the counter in green (using color pair 3) before reverting to the default (using color pair 1).
        """
        if new > old:
            for count in range(old + 1, new + 1):
                stdscr.addstr(
                    self.INFO_ROW,
                    2,
                    f"Selected Packages: {count} ",
                    curses.A_BOLD | curses.color_pair(3),
                )
                stdscr.refresh()
                curses.napms(300)  # increased delay for noticeable flash
                stdscr.addstr(
                    self.INFO_ROW,
                    2,
                    f"Selected Packages: {count} ",
                    curses.A_BOLD | curses.color_pair(1),
                )
                stdscr.refresh()
                curses.napms(100)
        else:
            stdscr.addstr(
                self.INFO_ROW,
                2,
                f"Selected Packages: {new} ",
                curses.A_BOLD | curses.color_pair(1),
            )
            stdscr.refresh()

    def draw_menu(self, stdscr: curses.window) -> None:
        curses.curs_set(0)
        curses.set_escdelay(25)
        curses.start_color()
        curses.use_default_colors()
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        curses.init_pair(1, curses.COLOR_WHITE, -1)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_MAGENTA, -1)
        curses.init_pair(5, curses.COLOR_BLUE, -1)

        stdscr.timeout(200)

        current_selection: int = self.menu_positions.get("distros", 0)
        scroll_offset: int = 0
        mode: str = "distros"

        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()

            # ──── CLEAR THE FULL BOTTOM LINE ────
            stdscr.move(height - 2, 0)
            stdscr.clrtoeol()

            # ──── IF PRELOAD THREAD STILL RUNNING, SHOW INDICATOR ────
            if (
                getattr(self, "_preload_thread", None)
                and self._preload_thread.is_alive()
            ):
                indicator = "🔴 Preloading..."
                x = max(0, width - len(indicator) - 1)
                stdscr.addstr(height - 2, x, indicator, curses.A_BOLD)

            # ──── HEADER / INFO / INSTRUCTIONS ────
            stdscr.addstr(self.HEADER_ROW, 2, self.header_text, curses.A_BOLD)
            stdscr.addstr(
                self.INFO_ROW,
                2,
                f"Selected Packages: {len(self.selected_packages)}",
                curses.A_BOLD,
            )
            stdscr.addstr(2, 40, self.menu_instructions, curses.A_DIM)

            # ──── BUILD menu_items BASED ON mode ────
            if mode == "distros":
                distro_menu = list(self.package_data.keys())
                menu_items: Sequence[Union[str, Tuple[str, Any, str]]] = distro_menu
                stdscr.addstr(4, 2, self.select_distro_text, curses.A_UNDERLINE)

            elif mode == "methods":
                methods_menu = list(self.package_data[self.selected_distro].keys()) + [
                    self.back_button_text
                ]
                menu_items = methods_menu
                stdscr.addstr(4, 2, f"Distro: {self.selected_distro}", curses.A_BOLD)
                stdscr.addstr(5, 2, self.select_method_text, curses.A_UNDERLINE)

            elif mode == "packages":
                categories = self.package_data[self.selected_distro][
                    self.selected_method
                ]
                packages_menu = [
                    (
                        self.get_category_display_text(
                            self.selected_distro, self.selected_method, cat
                        ),
                        cat,
                        "category",
                    )
                    for cat in categories.keys()
                ] + [(self.back_button_text, "", "back")]
                menu_items = packages_menu
                stdscr.addstr(
                    4,
                    2,
                    f"Distro: {self.selected_distro} | Method: {self.selected_method}",
                    curses.A_BOLD,
                )
                stdscr.addstr(5, 2, self.select_category_text, curses.A_UNDERLINE)

            else:  # mode == "category"
                _, pkg_list = self.get_category_data(
                    self.selected_distro, self.selected_method, self.current_category
                )
                category_menu: Sequence[Union[str, Tuple[str, Any, str]]] = (
                    [(self.install_button_text, None, "install")]
                    + [
                        (self.get_package_display_text(pkg), pkg, "package")
                        for pkg in pkg_list
                    ]
                    + [(self.back_button_text, None, "back")]
                )
                menu_items = category_menu
                stdscr.addstr(
                    4,
                    2,
                    f"Category: {self.current_category} | Packages: {len(pkg_list)}",
                    curses.A_BOLD,
                )
                stdscr.addstr(5, 2, self.select_package_text, curses.A_UNDERLINE)

            # ──── FOOTER ────
            stdscr.addstr(height - 1, 2, self.footer_text, curses.A_DIM)

            stdscr.refresh()

            # ──── HANDLE SCROLLING AND DRAW ITEMS ────
            max_items = height - self.MENU_START_ROW - 2
            if current_selection < scroll_offset:
                scroll_offset = current_selection
            elif current_selection >= scroll_offset + max_items:
                scroll_offset = current_selection - max_items + 1

            if len(menu_items) > max_items:
                visible = min(len(menu_items) - scroll_offset, max_items)
                scroll_info = f"Showing {scroll_offset + 1}-{scroll_offset + visible} of {len(menu_items)}"
                stdscr.addstr(
                    self.MENU_START_ROW + visible, 4, scroll_info, curses.A_DIM
                )

            for idx in range(
                scroll_offset, min(len(menu_items), scroll_offset + max_items)
            ):
                item = menu_items[idx]
                if isinstance(item, tuple):
                    item_type = item[2]
                    if item_type in ("install", "back"):
                        display_str = item[0]
                        attr = curses.color_pair(5)
                    elif item_type == "package":
                        pkg_obj = item[1]
                        base_text = item[0]
                        pkg_name = self.get_pkg_name(pkg_obj)
                        if self.is_package_installed(self.selected_method, pkg_name):
                            display_str = (
                                f"{self.CATEGORY_MARKER_INSTALLED} {base_text}"
                            )
                            attr = curses.color_pair(2)
                        else:
                            if pkg_name in self.selected_packages:
                                display_str = f"{self.PACKAGE_SELECTED} {base_text}"
                                attr = curses.color_pair(3)
                            else:
                                display_str = f"{self.PACKAGE_UNSELECTED} {base_text}"
                                attr = curses.A_NORMAL
                    else:
                        display_str = item[0]
                        attr = curses.A_NORMAL
                else:
                    display_str = (
                        "> " + item if idx == current_selection else "  " + item
                    )
                    attr = curses.A_NORMAL
                    if mode in ("methods", "packages") and (
                        isinstance(item, str) and item == self.back_button_text
                    ):
                        attr = curses.color_pair(5)
                if idx == current_selection:
                    attr |= curses.A_REVERSE
                try:
                    stdscr.addstr(
                        self.MENU_START_ROW + idx - scroll_offset, 4, display_str, attr
                    )
                except curses.error:
                    pass

            stdscr.refresh()
            k = stdscr.getch()

            if k == curses.KEY_MOUSE:
                try:
                    _id, mx, my, _z, bstate = curses.getmouse()
                except Exception:
                    continue
                if (
                    self.MENU_START_ROW
                    <= my
                    < self.MENU_START_ROW
                    + min(len(menu_items) - scroll_offset, max_items)
                ):
                    current_selection = scroll_offset + (my - self.MENU_START_ROW)
                    if bstate & curses.BUTTON1_CLICKED:
                        k = ord("\n")
                    else:
                        continue

            if k == ord("q"):
                # tally installed vs total
                methods = self.package_data.get(self.selected_distro, {})
                cats = methods.get(self.selected_method, {})
                total = sum(
                    len(
                        self.get_category_data(
                            self.selected_distro, self.selected_method, cat
                        )[1]
                    )
                    for cat in cats
                )
                installed = sum(
                    1
                    for cat in cats
                    for pkg in self.get_category_data(
                        self.selected_distro, self.selected_method, cat
                    )[1]
                    if self.is_package_installed(
                        self.selected_method, self.get_pkg_name(pkg)
                    )
                )
                # single-line prompt (no '\n')
                prompt = (
                    f"{installed}/{total} packages installed. Exit and clear screen?"
                )
                if self.confirm_action(stdscr, prompt):
                    self.nice_exit_popup(stdscr)
                    break
                else:
                    # user said No, go back into the menu
                    continue
            elif k == ord("l") or k == ord("L"):
                self.list_installed_packages(stdscr)
            elif k in (self.key_escape, curses.KEY_LEFT, ord("b"), ord("B")):
                if k in (self.key_escape, curses.KEY_LEFT, ord("b"), ord("B")):
                    self.menu_positions[mode] = current_selection
                    if mode == "methods":
                        mode = "distros"
                    elif mode == "packages":
                        mode = "methods"
                    elif mode == "category":
                        mode = "packages"
                # restore last cursor for new mode
                current_selection = self.menu_positions.get(mode, 0)
                scroll_offset = 0
            elif k == curses.KEY_UP:
                current_selection = (current_selection - 1) % len(menu_items)
            elif k == curses.KEY_DOWN:
                current_selection = (current_selection + 1) % len(menu_items)
            elif k in (ord("\n"), curses.KEY_RIGHT):
                if mode == "distros":
                    self.selected_distro = menu_items[current_selection]  # type: ignore
                    mode = "methods"
                    current_selection = 0
                    scroll_offset = 0
                elif mode == "methods":
                    if menu_items[current_selection] == self.back_button_text:
                        mode = "distros"
                    else:
                        self.selected_method = menu_items[current_selection]  # type: ignore
                        mode = "packages"
                    current_selection = 0
                    scroll_offset = 0
                elif mode == "packages":
                    current_item = menu_items[current_selection]
                    if isinstance(current_item, tuple) and current_item[2] == "back":
                        mode = "methods"
                    else:
                        self.current_category = current_item[1]  # type: ignore
                        mode = "category"
                    current_selection = 0
                    scroll_offset = 0
                elif mode == "category":
                    current_item = menu_items[current_selection]
                    if isinstance(current_item, tuple) and current_item[2] == "install":
                        self.install_category_packages(stdscr)
                        current_selection = 0
                        scroll_offset = 0
                    elif isinstance(current_item, tuple) and current_item[2] == "back":
                        mode = "packages"
                        current_selection = 0
                        scroll_offset = 0
                    elif (
                        isinstance(current_item, tuple) and current_item[2] == "package"
                    ):
                        pkg_obj = current_item[1]
                        pkg_name = self.get_pkg_name(pkg_obj)
                        if not self.is_package_installed(
                            self.selected_method, pkg_name
                        ):
                            if pkg_name in self.selected_packages:
                                self.selected_packages.remove(pkg_name)
                            else:
                                self.selected_packages.add(pkg_name)
                        else:
                            self.show_temp_message(
                                stdscr,
                                f"{pkg_name} is already installed. Press 'I' for info.",
                            )
            elif k == ord(" ") or k == ord("\n"):
                if mode == "packages":
                    current_item = menu_items[current_selection]
                    if isinstance(current_item, tuple) and current_item[2] == "back":
                        continue
                    display_text = (
                        current_item[0]
                        if isinstance(current_item, tuple)
                        else current_item
                    )
                    try:
                        cat_name = (
                            display_text.split(" ", 1)[1].split("(", 1)[0].strip()
                        )
                    except Exception:
                        cat_name = display_text
                    self.current_category = str(cat_name)
                    _, cat_pkgs = self.get_category_data(
                        self.selected_distro,
                        self.selected_method,
                        self.current_category,
                    )
                    remaining = [
                        self.get_pkg_name(pkg)
                        for pkg in cat_pkgs
                        if not self.is_package_installed(
                            self.selected_method, self.get_pkg_name(pkg)
                        )
                    ]
                    if remaining and all(
                        pkg in self.selected_packages for pkg in remaining
                    ):
                        for pkg in remaining:
                            self.selected_packages.discard(pkg)
                    else:
                        for pkg in remaining:
                            self.selected_packages.add(self.get_pkg_name(pkg))
                    new_count = len(self.selected_packages)
                    if new_count != self.last_selected_count:
                        self.animate_selected_count(
                            stdscr, self.last_selected_count, new_count
                        )
                        self.last_selected_count = new_count
            elif k == ord("i"):
                if self.selected_packages:
                    self.install_selected_packages(stdscr)
                    break
            elif k == ord("I"):
                if (
                    mode == "category"
                    and isinstance(menu_items[current_selection], tuple)
                    and menu_items[current_selection][2] == "package"
                ):
                    pkg_obj = menu_items[current_selection][1]
                    pkg_name = self.get_pkg_name(pkg_obj)
                    if self.is_package_installed(self.selected_method, pkg_name):
                        self.show_package_info(stdscr, pkg_name, self.selected_method)
                    else:
                        self.show_temp_message(stdscr, f"{pkg_name} is not installed.")
            elif k == ord("R"):
                if (
                    mode == "category"
                    and isinstance(menu_items[current_selection], tuple)
                    and menu_items[current_selection][2] == "package"
                ):
                    pkg_obj = menu_items[current_selection][1]
                    pkg_name = self.get_pkg_name(pkg_obj)
                    self.uninstall_individual_package(stdscr, pkg_name)
        curses.endwin()

    # -------------------------------------------------------------------------
    # Run the application.
    # -------------------------------------------------------------------------
    def run(self) -> None:
        import os

        try:
            curses.wrapper(self.draw_menu)
        except curses.error:
            print("Curses error: Unable to initialize curses.")
            try:
                curses.endwin()
            except Exception:
                print("Curses error: Unable to end window.")
            finally:
                print("\033[H\033[J", end="")  # Clear terminal
                print("\033[H\033[0J")  # Move cursor to the bottom
                print("Installed packages:")
                for package in self.selected_packages:
                    print(f"  ✅ {package.strip()}")
                print("Finished installing packages, have a nice day!")
                os._exit(0)


# =============================================================================
# Main entry point.
# =============================================================================
def main() -> None:
    app = PackageInstallerApp()
    app.run()


if __name__ == "__main__":

    def signal_handler(sig, frame) -> None:
        print("\nInterrupted! Exiting gracefully...")
        sys.exit(0)
        curses.endwin()

    signal.signal(signal.SIGINT, signal_handler)
    try:
        main()
    except KeyboardInterrupt:
        curses.endwin()
        print("\nInterrupted! Exiting gracefully...")
        sys.exit(0)
