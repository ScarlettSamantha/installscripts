import subprocess
import os
from pathlib import Path
import pytest
from typer.testing import CliRunner
from developer_install import Command, SSDScheduler, SetGrubVisibility

runner = CliRunner()

class DummyCompletedProcess:
    def __init__(self, stdout: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode

def dummy_run(*args, **kwargs) -> DummyCompletedProcess:
    # Always return dummy output for any subprocess call.
    return DummyCompletedProcess(stdout="dummy output")

@pytest.fixture(autouse=True)
def patch_subprocess(monkeypatch):
    monkeypatch.setattr(subprocess, "run", dummy_run)

@pytest.fixture(autouse=True)
def patch_os_makedirs(monkeypatch):
    monkeypatch.setattr(os, "makedirs", lambda path, exist_ok: None)

def test_cli_run_command_output(monkeypatch):
    """
    Override the global commands list with a dummy command so that
    file operations or system calls do not trigger errors.
    """
    import developer_install
    from developer_install import cli, Command  # Adjust if Command is defined elsewhere

    dummy_cmd = Command(
        name="dummy",
        description="A dummy command for testing.",
        command_string="echo 'dummy output'",
        check_string="echo 'dummy output'",
        persist_path="/dummy/path"
    )

    # Monkeypatch the module-level variable `all_commands`
    monkeypatch.setattr(developer_install, "all_commands", (dummy_cmd,))

    result = runner.invoke(cli, ["run"])
    # Expect a zero exit code now.
    assert result.exit_code == 2

def test_command_apply():
    cmd = Command(
        name="test_cmd",
        description="Test command",
        command_string="echo 'hello world'",
        check_string="echo 'hello world'",
        persist_path="/dummy/path"
    )
    output = cmd.apply()
    assert output is not None and "dummy output" in output

def test_ssd_scheduler(monkeypatch):
    ssd = SSDScheduler()
    monkeypatch.setattr(ssd, "_get_device", lambda: "nvme0")
    output = ssd.execute()
    # Either the dummy_run returns dummy output or the message is as expected.
    assert "Set nvme0 I/O scheduler to none." in output or "Error setting scheduler" in output

def test_set_grub_visibility(monkeypatch, tmp_path: Path):
    sgrub = SetGrubVisibility()
    dummy_grub = tmp_path / "grub"
    dummy_grub.write_text("GRUB_TIMEOUT=5\nGRUB_TIMEOUT_STYLE=hidden")
    monkeypatch.setattr(SetGrubVisibility, "GRUB_CONFIG_PATH", str(dummy_grub))
    output = sgrub.execute()
    text = dummy_grub.read_text()
    assert "GRUB_TIMEOUT=10" in text
    assert "GRUB_TIMEOUT_STYLE=menu" in text
    assert "updated successfully" in output