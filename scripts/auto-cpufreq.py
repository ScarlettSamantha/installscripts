import os
import io
from typing import Dict, List

class AutoCpufreq:
    
    SCALING_GOVERNORS_PATH: str = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors"
    SCALING_EPP_PATH: str = "/sys/devices/system/cpu/cpu0/cpufreq/energy_performance_available_preferences"
    SCALING_MIN_FREQ_PATH: str = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq"
    SCALING_MAX_FREQ_PATH: str = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq"
    TURBO_PATH: str = "/sys/devices/system/cpu/intel_pstate/no_turbo"
    PLATFORM_PROFILES_PATH: str = "/sys/firmware/acpi/platform_profile_choices"
    
    DEFAULT_BATTERY_SETTINGS = {
        "bat_gov": "powersave",
        "bat_epp": "power",
        "bat_epb": "balance_power",
        "bat_min_freq": "400000",
        "bat_max_freq": "800000",
        "bat_turbo": "auto",
        "bat_thresholds": "true",
        "bat_start_threshold": "20",
        "bat_stop_threshold": "80",
    }

    def __init__(self):
        self.temp_dir: str = "/tmp/auto-cpufreq"
        self.git_url: str = "https://github.com/AdnanHodzic/auto-cpufreq.git"
        self.install_script: str = "auto-cpufreq-installer"
        self.config_file: str = "/etc/auto-cpufreq.conf"

        self.config_template_file: str = "auto-cpufreq.template.conf"
        self.config_template_folder: str = os.path.join(os.path.dirname(__file__), 'configs')
        self.config_template: str = os.path.join(self.config_template_folder, self.config_template_file)

    def install(self) -> None:
        os.system(f"git clone {self.git_url} {self.temp_dir}")
        os.system(f"cd {self.temp_dir} && chmod +x {self.install_script} && sudo ./{self.install_script}")
        os.system(f"rm -rf {self.temp_dir}")
        
    @staticmethod
    def read_system_file(file_path: str, split_values: bool = False) -> List[str] | str:
        """
        Reads the content of a system file.

        Args:
            file_path (str): The path to the system file.
            split_values (bool): Whether to split the content into a list of values.

        Returns:
            List[str] or str: The content of the file as a list or string.
        """
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as file:
                    content = file.read().strip()
                    return content.split() if split_values else content
            except PermissionError:
                return f"Permission denied: {file_path}"
            except Exception as e:
                return f"Error reading {file_path}: {e}"
        else:
            return f"File not found: {file_path}"

    @property
    def battery_settings(self) -> Dict[str, str]:
        """
        Get the battery settings dynamically, falling back to defaults if not set.

        Returns:
            Dict[str, str]: Battery settings.
        """
        governors = self.read_system_file(self.SCALING_GOVERNORS_PATH, split_values=True)
        epps = self.read_system_file(self.SCALING_EPP_PATH, split_values=True)
        
        return {
            "bat_gov": governors[0] if governors else self.DEFAULT_BATTERY_SETTINGS["bat_gov"],
            "bat_epp": epps[0] if epps else self.DEFAULT_BATTERY_SETTINGS["bat_epp"],
            "bat_epb": self.DEFAULT_BATTERY_SETTINGS["bat_epb"],
            "bat_min_freq": self.read_system_file(self.SCALING_MIN_FREQ_PATH) or self.DEFAULT_BATTERY_SETTINGS["bat_min_freq"],
            "bat_max_freq": self.read_system_file(self.SCALING_MAX_FREQ_PATH) or self.DEFAULT_BATTERY_SETTINGS["bat_max_freq"],
            "bat_turbo": self.DEFAULT_BATTERY_SETTINGS["bat_turbo"],
            "bat_thresholds": self.DEFAULT_BATTERY_SETTINGS["bat_thresholds"],
            "bat_start_threshold": self.DEFAULT_BATTERY_SETTINGS["bat_start_threshold"],
            "bat_stop_threshold": self.DEFAULT_BATTERY_SETTINGS["bat_stop_threshold"],
        }

    def compile_settings(self) -> str:
        template = io.open(self.config_template, "r").read()
        
        config_values = {
            "charge_gov": "performance",
            "charge_epp": "performance",
            "charge_epb": "balance_performance",
            "charge_profile": "performance",
            "charge_min_freq": "800000",
            "charge_max_freq": "1000000",
            "charge_turbo": "auto",
            **self.battery_settings
        }

        for key, value in config_values.items():
            placeholder = f"{{{{{key}}}}}"
            template = template.replace(placeholder, str(value) if value is not None else "")
        
        return template
