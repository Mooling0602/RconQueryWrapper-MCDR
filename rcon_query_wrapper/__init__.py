from concurrent.futures import ThreadPoolExecutor
from mcdreforged.api.types import PluginServerInterface
from rcon_query_wrapper.utils import check_before_query
from typing import Callable, Optional


rcon_fine: bool = False


def on_load(server: PluginServerInterface, prev_module):
    server.logger.info("Initializing RconQueryWrapper and checking rcon status...")
    global rcon_fine
    rcon_fine = check_before_query()
    server.logger.info("Cached rcon usability.")
    if not rcon_fine:
        server.logger.error("Rcon may be not uasable, please check your configuration and connection!")

def rcon_query_wrapper(server: PluginServerInterface, command: str) -> str | None:
    if not rcon_fine:
        if not check_before_query():
            return None
    return query_rcon_result(server, command)
    


def query_rcon_result(server: PluginServerInterface, command: str) -> str | None:
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(server.rcon_query, command)
        try:
            result = future.result(timeout=5)
        except TimeoutError:
            if server.get_mcdr_language() == "zh_cn":
                server.logger.warning("RCON查询超时，需要重建MCDR与服务端之间的连接。")
            else:
                server.logger.warning("RCON query timeout, need to reopen the connection between MCDR and the server.")
            try:
                server._mcdr_server.connect_rcon()
                result = future.result(timeout=5)
            except TimeoutError:
                if server.get_mcdr_language() == "zh_cn":
                    raise TimeoutError("RCON查询长时间无响应！")
                else:
                    raise TimeoutError("Long time no response for RCON query!")
    return result