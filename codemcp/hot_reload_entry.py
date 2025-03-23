#!/usr/bin/env python3

import asyncio
import contextlib
import functools
import logging
import os
import sys
from asyncio import Queue, Task
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp import FastMCP

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
        self._task: Optional[Task] = None
        self._command_queue: Queue = Queue()
        self._response_queue: Queue = Queue()
        self._running = False
        self._session: Optional[ClientSession] = None

    async def start(self) -> None:
        """Start the background task if not already running."""
        if self._task is None or self._task.done():
            self._running = True
            self._task = asyncio.create_task(self._run_manager_task())
            # Wait for the context to be fully initialized
            await self._response_queue.get()

    async def stop(self) -> None:
        """Stop the background task and clean up resources."""
        if self._task and not self._task.done():
            self._running = False
            await self._command_queue.put(("stop", None))
            await self._task

    async def call_tool(self, **kwargs) -> str:
        """Call the codemcp tool in the subprocess."""
        if not self._running:
            await self.start()

        await self._command_queue.put(("call", kwargs))
        result = await self._response_queue.get()

        if isinstance(result, Exception):
            raise result
        return result

    async def _run_manager_task(self) -> None:
        """Background task that owns and manages the AsyncExitStack lifecycle."""
        mgr = contextlib.AsyncExitStack()
        try:
            # Initialize the context
            await mgr.__aenter__()

            # Setup stdio connection to main.py
            server_params = StdioServerParameters(
                command=sys.executable,  # Use the same Python interpreter
                args=[
                    os.path.join(os.path.dirname(__file__), "__main__.py")
                ],  # Use __main__
                env=os.environ.copy(),  # Pass current environment variables
            )

            read, write = await mgr.enter_async_context(stdio_client(server_params))
            self._session = await mgr.enter_async_context(ClientSession(read, write))
            await self._session.initialize()

            # Signal that initialization is complete
            await self._response_queue.put("initialized")

            # Process commands until told to stop
            while self._running:
                try:
                    command, args = await self._command_queue.get()

                    if command == "stop":
                        break

                    if command == "call" and self._session:
                        result = await self._session.call_tool(
                            "codemcp", arguments=args
                        )
                        await self._response_queue.put(result)

                except Exception as e:
                    logging.error("Error in hot reload manager task", exc_info=True)
                    await self._response_queue.put(e)

        except Exception as e:
            logging.error("Error initializing hot reload context", exc_info=True)
            await self._response_queue.put(e)

        finally:
            # Clean up resources properly
            try:
                await mgr.__aexit__(None, None, None)
            except Exception:
                logging.error("Error cleaning up hot reload context", exc_info=True)
            self._running = False
            self._session = None


# Global singleton manager
_MANAGER = HotReloadManager()


async def aexit():
    """Stop the hot reload manager and clean up resources."""
    await _MANAGER.stop()


@mcp.tool()
@functools.wraps(original_codemcp)  # This copies the signature and docstring
async def codemcp(**kwargs) -> str:
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

    try:
        # Register cleanup function for when the event loop exits
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(shutdown()))
        loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(shutdown()))

        # Run MCP server
        mcp.run()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        logging.info("Received keyboard interrupt, shutting down...")
        asyncio.run(shutdown())


async def shutdown():
    """Perform cleanup when shutting down."""
    logging.info("Shutting down hot reload manager...")
    await _MANAGER.stop()
    logging.info("Hot reload manager shut down successfully")


if __name__ == "__main__":
    import signal

    run()
