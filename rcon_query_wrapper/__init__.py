# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring, line-too-long
from typing import Optional, Callable, Any
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from mcdreforged.api.types import PluginServerInterface, ServerInterface, CommandSource
from mcdreforged.api.command import SimpleCommandBuilder, CommandContext, QuotableText
from mcdreforged.api.decorator import new_thread
from rcon_query_wrapper.utils import check_before_query, is_rcon_config_match, psi


builder = SimpleCommandBuilder()
rcon_fine: bool = False


@builder.command('!!@rcon <command>')
def on_command(src: CommandSource, ctx: CommandContext):
    server: ServerInterface = src.get_server()
    result = rcon_query_wrapper(server, ctx['command'])
    server.logger.info(f"Rcon result:\n{result}")

@builder.command('!!@rcon reconnect')
def on_reconnect_rcon(src: CommandSource | PluginServerInterface | ServerInterface, ctx: Optional[CommandContext] = None):  # pylint: disable=unused-argument
    server: ServerInterface |PluginServerInterface | None = None
    if isinstance(src, CommandSource):
        server = src.get_server()
    else:
        server = src
    if server:
        server._mcdr_server.connect_rcon()  # pylint: disable=protected-access


@builder.command('!!@rcon debug check_config')
def on_debug_check_config(src: CommandSource, ctx: CommandContext):  # pylint: disable=unused-argument
    server: ServerInterface = src.get_server()
    if server.is_rcon_running():
        _is_rcon_config_match = is_rcon_config_match()
        if not _is_rcon_config_match:
            server.logger.warning("Rcon is working but configuration may wrong, you should fix it!")
            server.logger.info("If you want to test rcon, use `!!@rcon <command>|\"<command_with_spaces>`\" to check simply.")
        else:
            server.logger.info("Rcon is working fine.")
    else:
        if not is_rcon_config_match():
            server.logger.error("Rcon configurations are misnatched, please edit your configuration!")
        else:
            on_reconnect_rcon(server)
            if not server.is_rcon_running():
                server.logger.error("Rcon is not working, please check your configuration and connection!")


@builder.command('!!@rcon debug builtin_query <command>')
@new_thread('MCDR: si.rcon_query')
def on_debug_builtin_query(src: CommandSource, ctx: CommandContext):  # pylint: disable=unused-argument
    server: ServerInterface = src.get_server()
    if check_before_query():
        result = server.rcon_query(ctx['command'])
        server.logger.info(result)


def on_load(server: PluginServerInterface, prev_module):  # pylint: disable=unused-argument
    builder.arg('command', QuotableText)
    builder.register(server)
    if server.is_server_startup():
        on_server_startup(server)


def on_server_startup(server: PluginServerInterface):  # pylint: disable=unused-argument
    server.logger.info("Initializing RconQueryWrapper and checking rcon status...")
    global rcon_fine  # pylint: disable=global-statement
    rcon_fine = check_before_query()
    server.logger.info("Cached rcon usability.")
    if not rcon_fine:
        server.logger.error("Rcon may be not uasable, please check your configuration and connection!")


def rcon_query(
        command: str,
        server: Optional[PluginServerInterface | ServerInterface] = None,
        command_result_arg: str = "result"
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _server = server if server is not None else psi
            result = rcon_query_wrapper(_server, command)
            kwargs[command_result_arg] = result
            return func(*args, **kwargs)
        return wrapper
    return decorator


def rcon_query_wrapper(server: PluginServerInterface | ServerInterface, command: str) -> str | None:
    if not rcon_fine:
        if not check_before_query():
            return None
    return query_rcon_result(server, command)


def query_rcon_result(server: PluginServerInterface | ServerInterface, command: str) -> str | None:
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
                server._mcdr_server.connect_rcon()  # pylint: disable=protected-access
                result = future.result(timeout=5)
            except TimeoutError as exc:
                if server.get_mcdr_language() == "zh_cn":
                    raise TimeoutError("RCON查询长时间无响应！") from exc
                else:
                    raise TimeoutError("Long time no response for RCON query!") from exc
    return result


@rcon_query('list', command_result_arg='rcon_result')
def test_rcon_query_decorator(
    server: PluginServerInterface | ServerInterface, rcon_result: str
):
    server.logger.info(rcon_result)


@builder.command('!!@rcon debug decorator')
def on_debug_decorator(src: CommandSource, ctx: Optional[CommandContext] = None):  # pylint: disable=unused-argument
    server = src.get_server()
    test_rcon_query_decorator(server)  # pylint: disable=no-value-for-parameter
