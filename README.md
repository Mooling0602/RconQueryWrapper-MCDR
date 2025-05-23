# RconQueryWrapper-MCDR
A wrapper for executing commands and get results with rcon in MCDR.

## Why you need this?
`ServerInterface.rcon_query(command: str)` is a very simple way to execute commands and get the results with rcon in MCDReforged.
> You need configure rcon connection in `/path/to/server/server.properties` and `/path/to/mcdr/config.yml` correctly first of all.

However, there's some unfixed issues with it:
- UNSTABLE: The rcon connection may be closed unexpectedly during MCDR server running, and it will not be reopened automatically because MCDR will not check for it.
> If you use Folia servers, you'll often get this issue.

- UNSAFE: The method may block the TaskExecutor thread if no response is received from the server, and cause WatchDog warning.
> Other plugins and works may also be affected.

With this wrapper, you can easily fix these issues and make your plugin more stable without doing extra works by yourself.

## How this wrapper works?
This wrapper is based on the `ServerInterface.rcon_query(command: str)` method, of course.

First, this plugin(this wrapper) uses a `ThreadPoolExecutor`(with 1 worker thread) to asynchronously run `PluginServerInterface.rcon_query(command)`, to avoid blocking the TaskExecutor during RCON operations.

Then, it waits up to 5 seconds for the result. If no response, it will log a warning to the console, but continue to wait for the response. In this case, plugin will try to use undocumented interfaces of MCDR for reopening the RCON connection between MCDR and the Minecraft server.

Most of the time, this wrapper will work well.

But if the RCON connection is still unavailable, or still no response received, after another 5 seconds, this wrapper will raise a `TimeoutError`.
> Raising errors may not affect your other plugins' and MCDR's work, and you can then try to check your configuration and connection.

## Usage
This plugin(wrapper) is designed for plugin developers, you developers can use it as a dependency, or copy the source code you need into your plugin. For the latter, no guides will be provided for it's not recommended.

If you want to import this wrapper as a dependency, please follow the guide.

### Development Guide
1. Edit your plugin's metadata(`mcdreforged.plugin.json`) and add this wrapper as a MCDR plugin dependency:
```json
{
    ...
    "dependencies": [
        "mcdreforged": ">=2.1.0",
        "rcon_query_wrapper": ">=0.0.1"
    ]
    ...
}
```

2. Import to your plugin:
```python
import rcon_query_wrapper
```

3. Use the function, here is an example:
```python
from mcdreforged.api.types import PluginServerInterface
from rcon_query_wrapper import rcon_query_wrapper


def your_function(server: PluginServerInterface):
    command: str = "list"
    rcon_q = rcon_query_wrapper()
    if rcon_q:
        result = rcon_q(server, command)
    server.logger.info(result)
```