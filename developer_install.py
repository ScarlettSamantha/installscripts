# app.py
"""
A CLI tool for executing and managing system configuration commands.

This module uses Typer to provide a command-line interface for executing,
persisting, and checking system configuration commands.
"""

from typing import Generator, Optional, Tuple, Union
import subprocess
import re
import os
import typer

cli = typer.Typer()

# === Command Classes ===

class ActionCommand:
    """Represents an action that can be executed instead of a static command string."""
    
    def __init__(self, action: Optional[str] = None) -> None:
        self.action = action  # Placeholder for actual command logic
        # You can optionally set these later:
        self.name: Optional[str] = None
        self.description: Optional[str] = None

    def execute(self) -> Optional[str]:
        """Executes the action and returns the output as a string."""
        return f"Executing action: {self.action}"

    def check(self) -> bool:
        return True

    def __str__(self) -> str:
        return self.action if self.action is not None else ""

class Command:
    def __init__(
        self,
        name: str,
        description: str,
        command_string: Union[str, ActionCommand],
        check_string: Optional[Union[str, ActionCommand]] = None,
        persist_path: Optional[str] = None,
    ) -> None:
        """
        :param name: The name of the configuration.
        :param description: Description of the configuration change.
        :param command_string: The actual command to apply (sysctl, shell command, or file modification).
        :param check_string: Optional command to verify the current setting.
        :param persist_path: Optional file path to persist configuration (e.g., /etc/sysctl.d/custom.conf).
        """
        self.name: str = name
        self.description: str = description
        self.command_string: Union[str, ActionCommand] = command_string
        self.check_string: Optional[Union[str, ActionCommand]] = check_string
        self.persist_path: Optional[str] = persist_path

    def apply(self) -> Optional[str]:
        """Applies the command (either sysctl, shell execution, or file writing)."""
        if isinstance(self.command_string, ActionCommand):
            return self.command_string.execute()
        elif self.command_string.startswith("fs.") or self.command_string.startswith("net."):
            return subprocess.run(
                f"sysctl -w {self.command_string}", shell=True, capture_output=True, text=True
            ).stdout
        else:
            return subprocess.run(
                self.command_string, shell=True, capture_output=True, text=True
            ).stdout

    def persist(self) -> str:
        """Persists the command to a system configuration file if a path is provided."""
        if not self.persist_path:
            return "No persistence path specified."

        try:
            os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
            with open(self.persist_path, "a") as f:
                f.write(f"{self.command_string}\n")
            return f"Persisted: {self.command_string} in {self.persist_path}"
        except PermissionError:
            return f"Permission denied: Run with sudo to persist settings in {self.persist_path}"

    def check(self) -> Optional[str]:
        """Checks if the configuration is applied."""
        if not self.check_string:
            return None
        if isinstance(self.check_string, ActionCommand):
            return self.check_string.execute()
        return subprocess.run(
            self.check_string, shell=True, capture_output=True, text=True
        ).stdout

CommandType = Union[Command, ActionCommand]
CommandTuple = Tuple[CommandType, ...]

class SSDScheduler(ActionCommand):
    def __init__(self) -> None:
        super().__init__()
        self.name = "SSD Scheduler"
        self.description = "Set I/O scheduler based on detected storage device (NVMe or SSD)"

    def _get_device(self) -> Optional[str]:
        """Detects primary storage device (either SATA SSD or NVMe)."""
        try:
            # Check for NVMe devices
            nvme_devices = [dev for dev in os.listdir("/sys/block/") if dev.startswith("nvme")]
            if nvme_devices:
                return nvme_devices[0]  # Return first NVMe device found

            # Check for SSDs (filtering out HDDs)
            with open("/sys/block/sda/queue/rotational", "r") as f:
                if f.read().strip() == "0":  # SSDs return 0, HDDs return 1
                    return "sda"
        except Exception:
            # Swallow exception details here; errors will be reported in execute()
            return None
        return None

    def execute(self) -> str:
        """Sets the I/O scheduler for the detected storage device and returns a status message."""
        device = self._get_device()
        if not device:
            return "No SSD or NVMe device detected."
        scheduler = "none" if device.startswith("nvme") else "mq-deadline"
        try:
            subprocess.run(
                ["sudo", "tee", f"/sys/block/{device}/queue/scheduler"],
                input=scheduler.encode(), check=True
            )
            return f"Set {device} I/O scheduler to {scheduler}."
        except subprocess.CalledProcessError as e:
            return f"Error setting scheduler: {e}"

    def result(self) -> bool:
        """Checks if the correct scheduler is applied."""
        device = self._get_device()
        if not device:
            return False
        try:
            with open(f"/sys/block/{device}/queue/scheduler", "r") as f:
                current_scheduler = f.read().strip()
                expected_scheduler = "[none]" if device.startswith("nvme") else "[mq-deadline]"
                return expected_scheduler in current_scheduler
        except Exception:
            return False

class GitCredentialStore(ActionCommand):
    def __init__(self, action: Optional[str] = None) -> None:
        super().__init__(action)
        self.name = "Git Credential Store"
        self.description = "Configure Git to store credentials globally"

    def execute(self) -> str:
        """Configures Git to store credentials."""
        result = subprocess.run(
            "git config --global credential.helper store", 
            shell=True, capture_output=True, text=True
        )
        return result.stdout.strip()

    def result(self) -> bool:
        """Verifies that Git's credential helper is set to 'store'."""
        result = subprocess.run(
            "git config --global credential.helper", 
            shell=True, capture_output=True, text=True
        )
        # Compare the output with the expected value
        return result.stdout.strip() == "store"

class SetGrubVisibility(ActionCommand):
    GRUB_CONFIG_PATH = "/etc/default/grub"

    def __init__(self) -> None:
        super().__init__()
        self.name = "Set GRUB Visibility"
        self.description = "Update GRUB config to show menu with a 10-second timeout"

    def execute(self) -> str:
        """Updates GRUB configuration to ensure the menu is visible with a 10-second timeout."""
        try:
            with open(self.GRUB_CONFIG_PATH, "r") as f:
                grub_config = f.read()

            # Update GRUB configuration settings
            grub_config = re.sub(r'GRUB_TIMEOUT=\d+', 'GRUB_TIMEOUT=10', grub_config)
            grub_config = re.sub(r'GRUB_TIMEOUT_STYLE=\w+', 'GRUB_TIMEOUT_STYLE=menu', grub_config)

            with open(self.GRUB_CONFIG_PATH, "w") as f:
                f.write(grub_config)

            # Update GRUB to apply changes
            subprocess.run(["sudo", "update-grub"], check=True)
            return "GRUB configuration updated successfully."
        except Exception as e:
            return f"Error updating GRUB: {e}"

    def result(self) -> bool:
        """Verifies that the GRUB configuration has been updated correctly."""
        try:
            with open(self.GRUB_CONFIG_PATH, "r") as f:
                grub_config = f.read()
            timeout_match = re.search(r'GRUB_TIMEOUT=10', grub_config)
            style_match = re.search(r'GRUB_TIMEOUT_STYLE=menu', grub_config)
            return bool(timeout_match and style_match)
        except Exception:
            return False

# The following line is kept for compatibility with previous iterations.
ssd_scheduler = ActionCommand

# === Command Configurations ===

inotify_commands: CommandTuple = (
    Command(
        "inotify.max_user_watches", 
        "Set max user watches", 
        "echo 'fs.inotify.max_user_watches = 32384' >> /etc/sysctl.conf && sysctl -p",
        check_string="sysctl fs.inotify.max_user_watches",
        persist_path="/etc/sysctl.conf"
    ),
    Command(
        "inotify.max_user_instances", 
        "Set max user instances", 
        "echo 'fs.inotify.max_user_instances = 512' >> /etc/sysctl.conf && sysctl -p",
        check_string="sysctl fs.inotify.max_user_instances",
        persist_path="/etc/sysctl.conf"
    ),
)

system_commands: CommandTuple = (
    Command(
        "Swappiness", 
        "Set vm.swappiness to 10", 
        "echo 'vm.swappiness=10' | tee /etc/sysctl.d/99-swappiness.conf && sysctl -p /etc/sysctl.d/99-swappiness.conf",
        check_string="sysctl vm.swappiness",
        persist_path="/etc/sysctl.d/99-swappiness.conf"
    ),
    Command(
        "Transparent HugePages", 
        "Enable Transparent HugePages", 
        "echo 'always' | tee /sys/kernel/mm/transparent_hugepage/enabled",
        check_string="cat /sys/kernel/mm/transparent_hugepage/enabled",
        persist_path="/etc/sysfs.conf"
    ),
)

vm_commands: CommandTuple = (
    Command(
        "dirty_ratio", 
        "Set vm.dirty_ratio to 2", 
        "echo 'vm.dirty_ratio=2' >> /etc/sysctl.conf && sysctl -p",
        check_string="sysctl vm.dirty_ratio",
        persist_path="/etc/sysctl.conf"
    ),
    Command(
        "background_ratio", 
        "Set vm.dirty_background_ratio to 10", 
        "echo 'vm.dirty_background_ratio=10' >> /etc/sysctl.conf && sysctl -p",
        check_string="sysctl vm.dirty_background_ratio",
        persist_path="/etc/sysctl.conf"
    ),
)


# Create GitCredentialStore and SSDScheduler instances with descriptions already set.
git_credential_store = GitCredentialStore("Git Credential Store")
ssd_scheduler_cmd = SSDScheduler()

git_commands: CommandTuple = (git_credential_store,)
storage_commands: CommandTuple = (ssd_scheduler_cmd,)

all_commands: CommandTuple = inotify_commands + system_commands + vm_commands + storage_commands + git_commands

# === Application ===

class App:
    def __init__(self, commands: CommandTuple) -> None:
        self.commands: CommandTuple = commands

    def process(self) -> Generator[str, None, None]:
        """
        Processes each command by executing it, persisting configurations (if applicable),
        and checking the applied settings. Yields CLI log messages with emoji feedback.
        """
        yield "🚀 Starting command execution..."
        for cmd in self.commands:
            # Use provided name and description if available.
            if isinstance(cmd, Command):
                name = cmd.name
                description = cmd.description
            else:
                name = cmd.name if hasattr(cmd, "name") and cmd.name else cmd.__class__.__name__
                description = cmd.description if hasattr(cmd, "description") and cmd.description else "No description provided."
            yield f"🔧 Executing '{name}': {description}"
            try:
                if isinstance(cmd, Command):
                    output = cmd.apply()
                else:
                    output = cmd.execute()
                if output and isinstance(output, str) and output.strip():
                    yield f"📄 Output: {output.strip()}"
            except Exception as e:
                yield f"❌ Error executing '{name}': {e}"
                continue

            if isinstance(cmd, Command) and cmd.persist_path:
                try:
                    persist_output = cmd.persist()
                    yield f"💾 Persistence: {persist_output}"
                except Exception as e:
                    yield f"❌ Error persisting '{name}': {e}"

            if hasattr(cmd, "result"):
                try:
                    check_output_raw = cmd.check()
                    # Enhanced check: if this is a Command with string-based command and check,
                    # try to extract the expected value and compare.
                    if isinstance(cmd, Command) and isinstance(cmd.command_string, str) and isinstance(cmd.check_string, str):
                        m_exp = re.search(r'([\w\.]+)\s*=\s*([^\s\'"]+)', cmd.command_string)
                        if m_exp:
                            key = m_exp.group(1)
                            expected_value = m_exp.group(2)
                            m_cur = re.search(rf'{re.escape(key)}\s*=\s*([^\s]+)', str(check_output_raw)) if check_output_raw is not None else None
                            if m_cur:
                                current_value = m_cur.group(1)
                                if current_value == expected_value:
                                    check_output = f"✅ ({current_value})"
                                else:
                                    check_output = f"❌ (expected: {expected_value}, got: {current_value})"
                            else:
                                check_output = str(check_output_raw).strip() if isinstance(check_output_raw, str) and check_output_raw is not None else "N/A"
                        else:
                            check_output = str(check_output_raw).strip() if check_output_raw is not None else "N/A"
                    elif isinstance(check_output_raw, bool):
                        check_output = "✅" if check_output_raw else "❌"
                    elif isinstance(check_output_raw, str):
                        check_output = check_output_raw.strip() if check_output_raw.strip() else "N/A"
                    else:
                        check_output = str(check_output_raw)
                    yield f"✅ Check: {check_output}"
                except Exception as e:
                    yield f"❌ Error checking '{name}': {e}"
            yield "-----------------------------------"
        yield "🎉 All commands executed."

# === Typer CLI Command ===

@cli.command(
    name="run",
    help=(
        "Execute system configuration commands.\n\n"
        "By default, this command will execute all configured commands (apply, persist, and then check).\n"
        "Use the --name (-n) option to run a specific command (the name matching is case-insensitive).\n"
        "Use the --check-only (-c) flag to run only the check routines and display the results in a formatted table."
    )
)
def run(
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Specify the name of the command to run. If omitted, all commands will be executed."
    ),
    check_only: bool = typer.Option(
        False,
        "--check-only",
        "-c",
        help="Run only the check function for each command and display the results in a table."
    )
) -> None:
    """
    Executes or checks system configuration commands.
    """
    if name is None:
        selected_commands = all_commands
    else:
        selected_commands = []
        for cmd in all_commands:
            cmd_name = cmd.name if hasattr(cmd, "name") and cmd.name else cmd.__class__.__name__
            if cmd_name.lower() == name.lower():
                selected_commands.append(cmd)
        if not selected_commands:
            typer.echo(f"❌ No command found with name '{name}'.")
            raise typer.Exit()


    if not check_only:
            typer.echo("🚀 Executing configuration commands...\n")
            app_instance = App(all_commands)
            for log in app_instance.process():
                typer.echo(log)
    else:
        typer.echo("🔍 Running check operations only...\n")
        # Build a list of rows: (Command, Description, Check Result)
        rows = []
        for cmd in selected_commands:
            cmd_name = cmd.name if hasattr(cmd, "name") and cmd.name else cmd.__class__.__name__
            description = cmd.description if hasattr(cmd, "description") and cmd.description else "No description provided."
            try:
                if hasattr(cmd, "check"):
                    result = cmd.check()
                    if isinstance(cmd, Command) and isinstance(cmd.command_string, str) and isinstance(cmd.check_string, str):
                        m_exp = re.search(r'([\w\.]+)\s*=\s*([^\s\'"]+)', cmd.command_string)
                        if m_exp and isinstance(result, str):
                            key = m_exp.group(1)
                            expected_value = m_exp.group(2)
                            m_cur = re.search(rf'{re.escape(key)}\s*=\s*([^\s]+)', result)
                            if m_cur:
                                current_value = m_cur.group(1)
                                if current_value == expected_value:
                                    check_output = f"✅ ({current_value})"
                                else:
                                    check_output = f"❌ (expected: {expected_value}, got: {current_value})"
                            else:
                                check_output = result.strip() if isinstance(result, str) and result else "N/A"
                        else:
                            check_output = result.strip() if isinstance(result, str) and result else "N/A"
                    elif isinstance(result, bool):
                        check_output = "✅" if result else "❌"
                    elif isinstance(result, str):
                        check_output = result.strip() if result.strip() else "N/A"
                    else:
                        check_output = str(result)
                else:
                    check_output = "N/A"
            except Exception as e:
                check_output = f"Error: {e}"
            rows.append((cmd_name, description, check_output))

        # Create table header.
        header = ("Command", "Description", "Check Result")
        # Calculate column widths.
        col_widths = [max(len(str(item)) for item in col) for col in zip(header, *rows)]
        
        # Create a horizontal separator.
        separator = " | ".join("-" * width for width in col_widths)
        
        # Print the header row.
        header_row = " | ".join(str(header[i]).ljust(col_widths[i]) for i in range(len(header)))
        typer.echo(header_row)
        typer.echo(separator)
        
        # Print each table row.
        for row in rows:
            row_line = " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
            typer.echo(row_line)
            
    

if __name__ == "__main__":
    cli()
    run(check_only=True)
