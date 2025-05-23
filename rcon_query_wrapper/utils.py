import javaproperties
import os

from enum import StrEnum, auto
from dataclasses import dataclass
from mcdreforged.api.all import ServerInterface


psi = ServerInterface.psi()


@dataclass
class RconConfig:
    enable: bool
    port: int
    password: str


class RconConfigType(StrEnum):
    """
    The path of the target file
    """
    MCDR = auto()
    SERVER = auto()


def get_rcon_config(type: RconConfigType | str) -> RconConfig | None:
    match type:
        case RconConfigType.MCDR:
            return RconConfig(
                enable=psi.get_mcdr_config().get("rcon", None).get("enable", None),
                port=psi.get_mcdr_config().get("rcon", None).get("port", None),
                password=psi.get_mcdr_config().get("rcon", None).get("password", None)
            )
        case RconConfigType.SERVER:
            server_prop_path = os.path.join(
                psi.get_mcdr_config().get("working_directory", None),
                "server.properties"
            )
            if not os.path.exists(server_prop_path):
                return None
            server_prop: dict | None = None
            try:
                with open(server_prop_path, "r") as f:
                    data = f.read()
                    server_prop = javaproperties.loads(s=data)
            except Exception as e:
                psi.logger.error("Unable to read server.properties in server directory.")
            config: RconConfig | None = None
            if server_prop is not None:
                config = RconConfig(
                    enable=server_prop.get("enable-rcon", None),
                    port=server_prop.get("rcon.port", None),
                    password=server_prop.get("rcon.password", None)
                )
            return config


def is_rcon_config_match() -> bool:
    mcdr_config: RconConfig | None = get_rcon_config(RconConfigType.MCDR)
    server_config: RconConfig | None = get_rcon_config(RconConfigType.SERVER)
    if mcdr_config == server_config:
        return True
    return False


def check_before_query() -> bool:
    if not psi.is_rcon_running():
        if not is_rcon_config_match():
            psi.logger.error("Rcon config is wrong, please fix it by yourself!")
        else:
            psi.reload_config_file(log=True)
            psi._mcdr_server.connect_rcon()
            if psi.is_rcon_running():
                return True
    return False