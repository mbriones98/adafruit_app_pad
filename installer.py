import platform
import os
from enum import Enum
from string import Template
from utils.constants import OS_MAC, OS_LINUX, OS_WINDOWS

class OperatingSystem(Enum):
    WINDOWS: str = "Windows"
    LINUX: str = "Linux"
    MACOS: str = "Darwin"

def create_init_files(os: str):
    substitution = { "OPERATING_SYSTEM": os}
    config = str()
    with open(f"config/initConfig.template", "r") as f:
        config = Template(f.read())
        config.substitute(substitution)

    with open("user.py", "w") as f:
        f.write(config)

def init_adafruit_app_pad():
    os = platform.system()
    match os:
        case OperatingSystem.WINDOWS.value:
            create_init_files(OS_WINDOWS)
        case OperatingSystem.LINUX.value:
            create_init_files(OS_LINUX)
        case OperatingSystem.MACOS.value:
            create_init_files(OS_MAC)
        case _:
            raise ValueError(f"Unknown operating system: {os}")