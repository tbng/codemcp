#!/usr/bin/env python3


import asyncio
import functools
import logging
import os
import sys
from asyncio import Future, Queue, Task
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union, cast

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent


# Define the ClientSession.call_tool result type
class CallToolResult(Protocol):
    """Protocol for objects returned by call_tool."""

    isError: bool
    content: Union[str, List[TextContent], Any]


# Add type information for ClientSession
if not hasattr(ClientSession, "__call_tool_typed__"):
    # Store original call_tool method
    setattr(ClientSession, "__call_tool_typed__", True)
    # Add type hints (this won't change runtime behavior, just helps type checking)

# Import the original codemcp function from main to clone its signature
from codemcp.main import (
    codemcp as original_codemcp,
)
from codemcp.main import (
    configure_logging as main_configure_logging,
)

# Initialize FastMCP server with the same name
mcp = FastMCP("codemcp")


class HotReloadManager:
    """
    Manages the lifecycle of the hot reload context in a dedicated background task.
    This ensures proper cleanup of async resources by having a single task own the
    context manager.
    """

    def __init__(self):
        self._task: Optional[Task[None]] = None
        self._request_queue: Optional[Queue[Tuple[str, Any, asyncio.Future[Any]]]] = (
            None
        )
        self._hot_reload_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".hot_reload"
        )
        self._last_hot_reload_mtime: Optional[float] = None
        self._check_hot_reload_file()

    def _check_hot_reload_file(self) -> bool:
        """
        Check if the .hot_reload file exists and if its mtime has changed.
        Returns True if a reload should be triggered, False otherwise.
        """
        if not os.path.exists(self._hot_reload_file):
            # If the file doesn't exist now but did before, we should reload
            if self._last_hot_reload_mtime is not None:
                logging.info("Hot reload file removed, triggering reload")
                self._last_hot_reload_mtime = None
                return True
            return False

        current_mtime = os.path.getmtime(self._hot_reload_file)

        # If we haven't recorded an mtime yet, store it and don't reload
        if self._last_hot_reload_mtime is None:
            self._last_hot_reload_mtime = current_mtime
            return False

        # If the mtime has changed, trigger a reload
        if current_mtime > self._last_hot_reload_mtime:
            logging.info(
                f"Hot reload file modified, triggering reload (mtime: {current_mtime})"
            )
            self._last_hot_reload_mtime = current_mtime
            return True

        return False

    async def start(self) -> None:
        """Start the background task if not already running."""
        # NB: done() checks for if the old event loop was cleaned up
        if self._task is None or self._task.done():
            # Create fresh queue for this run
            self._request_queue = Queue()

            # Create the task with explicit parameters
            self._task = asyncio.create_task(
                self._run_manager_task(self._request_queue)
            )

    async def stop(self) -> None:
        """Stop the background task and clean up resources."""
        if self._task and not self._task.done() and self._request_queue:
            # Create a future for the stop command
            stop_future: Future[bool] = asyncio.Future()

            # Get a local reference to the queue and task before clearing
            request_queue = self._request_queue
            task = self._task

            # Clear request_queue BEFORE any awaits to prevent race conditions
            self._request_queue = None

            # Now it's safe to do awaits since new messages can't be added to self._request_queue
            # TODO: You don't need stop_future, the await task is enough
            await request_queue.put(("stop", None, stop_future))
            await stop_future
            await task

    async def call_tool(self, **kwargs: Any) -> str:
        """Call the codemcp tool in the subprocess."""
        # Check if we need to reload based on .hot_reload file
        if (
            self._check_hot_reload_file()
            and self._task is not None
            and not self._task.done()
        ):
            logging.info("Stopping hot reload manager due to .hot_reload file change")
            await self.stop()

        # Start if needed
        if self._task is None or self._task.done() or self._request_queue is None:
            await self.start()

        # Create a future for this specific request
        response_future: Future[str] = asyncio.Future()

        # Send the request and its associated future to the manager task
        if self._request_queue is not None:
            await self._request_queue.put(("call", kwargs, response_future))

        # Wait for the response
        return await response_future

    async def _run_manager_task(
        self, request_queue: Queue[Tuple[str, Any, asyncio.Future[Any]]]
    ) -> None:
        """
        Background task that owns and manages the async context managers lifecycle.

        Parameters:
            request_queue: Queue to receive commands from
        """
        # Setup stdio connection to main.py
        server_params = StdioServerParameters(
            command=sys.executable,  # Use the same Python interpreter
            args=[
                os.path.join(os.path.dirname(__file__), "__main__.py")
            ],  # Use __main__
            env=os.environ.copy(),  # Pass current environment variables
        )

        # Use nested async with statements to properly manage context
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()

                # Process commands until told to stop
                while True:
                    command, args, future = await request_queue.get()
                    try:
                        if command == "stop":
                            future.set_result(True)
                            break

                        if command == "call":
                            # Use explicit cast for tool_args to help with type checking
                            tool_args = cast(Dict[str, Any], args)

                            # Get the raw result from call_tool
                            # We avoid type annotations on the intermediate result
                            call_result = await session.call_tool(  # type: ignore
                                name="codemcp", arguments=tool_args
                            )

                            # Apply our protocol to the result
                            result = cast(CallToolResult, call_result)
                            # This is the only error case FastMCP can
                            # faithfully re-propagate, see
                            # https://github.com/modelcontextprotocol/python-sdk/issues/348
                            if result.isError:
                                match result.content:
                                    case [TextContent(text=err)]:
                                        future.set_exception(RuntimeError(err))
                                    case _:
                                        future.set_exception(
                                            RuntimeError("Unknown error")
                                        )
                            future.set_result(result.content)

                    except Exception as e:
                        logging.error("Error in hot reload manager task", exc_info=True)
                        if not future.done():
                            future.set_exception(e)


# Global singleton manager
_MANAGER = HotReloadManager()


async def aexit():
    """Stop the hot reload manager and clean up resources."""
    await _MANAGER.stop()


@mcp.tool()
@functools.wraps(original_codemcp)  # This copies the signature and docstring
async def codemcp(**kwargs: Any) -> str:
    """This is a wrapper that forwards all tool calls to the codemcp/main.py process.
    This allows for hot-reloading as main.py will be reloaded on each call.

    Arguments are the same as in main.py's codemcp tool.
    """
    configure_logging()
    try:
        # Use the HotReloadManager to handle the context and session lifecycle
        return await _MANAGER.call_tool(**kwargs)
    except Exception:
        logging.error("Exception in hot_reload_entry.py", exc_info=True)
        raise


def configure_logging():
    """Import and use the same logging configuration from main module"""
    main_configure_logging("codemcp_hot_reload.log")


def run():
    """Run the MCP server with hot reload capability."""
    configure_logging()
    logging.info("Starting codemcp with hot reload capability")
    mcp.run()


if __name__ == "__main__":
    run()
