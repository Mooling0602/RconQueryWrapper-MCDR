# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring, line-too-long
import os

from dataclasses import dataclass
from enum import StrEnum, auto
from mcdreforged.api.all import ServerInterface

import javaproperties


psi = ServerInterface.psi()


@dataclass
class RconConfig:
    enable: bool
    port: int
    password: str

    def __post_init__(self):
        if not isinstance(self.enable, bool):
            raise TypeError(f"enable must be a boolean, got {type(self.enable)}")
        if not isinstance(self.port, int):
            raise TypeError(f"port must be an integer, got {type(self.port)}")
        if not isinstance(self.password, str):
            raise TypeError(f"password must be a string, got {type(self.password)}")
        if self.port <= 0 or self.port > 65535:
            raise ValueError(f"port must be between 1 and 65535, got {self.port}")


class RconConfigType(StrEnum):
    """
    The path of the target file
    """
    MCDR = auto()
    SERVER = auto()


def get_rcon_config(config_type: RconConfigType | str) -> RconConfig | None:
    match config_type:
        case RconConfigType.MCDR:
            mcdr_config: dict = psi.get_mcdr_config()
            return RconConfig(
                enable=mcdr_config["rcon"]["enable"],
                port=mcdr_config["rcon"]["port"],
                password=mcdr_config["rcon"]["password"]
            )
        case RconConfigType.SERVER:
            server_path: str = str(psi.get_mcdr_config().get("working_directory", None))
            server_prop_path = os.path.join(
                server_path,
                "server.properties"
            )
            if not os.path.exists(server_prop_path):
                psi.logger.error(f"server.properties is not found in configured working_directory {server_prop_path}")
                return None
            server_prop: dict | None = None
            try:
                with open(server_prop_path, "r") as f:  # pylint: disable=unspecified-encoding
                    data = f.read()
                    server_prop = javaproperties.loads(s=data)
            except Exception as e:  # pylint: disable=broad-except
                psi.logger.error(f"Unable to read server.properties in server directory: {e}")
            config: RconConfig | None = None
            if server_prop is not None:
                config = RconConfig(
                    enable=bool(server_prop.get("enable-rcon", None)),
                    port=int(server_prop.get("rcon.port", 0)),
                    password=str(server_prop.get("rcon.password", None))
                )
            return config


def is_rcon_config_match() -> bool:
    try:
        mcdr_config: RconConfig | None = get_rcon_config(RconConfigType.MCDR)
        server_config: RconConfig | None = get_rcon_config(RconConfigType.SERVER)
        if mcdr_config == server_config:
            return True
    except Exception as e:  # pylint: disable=broad-exception-caught
        psi.logger.error(f"Error while getting rcon config: {e}")
        return False
    return False


def check_before_query() -> bool:
    if not psi.is_rcon_running():
        if not is_rcon_config_match():
            psi.logger.error("Rcon config is wrong, please fix it by yourself!")
        else:
            psi.reload_config_file(log=True)
            psi._mcdr_server.connect_rcon()  # pylint: disable=protected-access
            if psi.is_rcon_running():
                return True
    else:
        return True
    return False
