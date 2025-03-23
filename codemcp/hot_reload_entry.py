#!/usr/bin/env python3

import asyncio
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
        self._request_queue: Optional[Queue] = None
        self._init_future: Optional[asyncio.Future] = None
        self._running = False
        self._session: Optional[ClientSession] = None

    async def start(self) -> None:
        """Start the background task if not already running."""
        if self._task is None or self._task.done():
            # Create fresh state for this run
            self._running = True
            self._request_queue = Queue()
            self._init_future = asyncio.Future()

            # Start task with explicit parameters to avoid accessing self
            request_queue = self._request_queue
            init_future = self._init_future

            # Create the task with explicit parameters
            self._task = asyncio.create_task(
                self._run_manager_task(request_queue, init_future)
            )

            # Wait for the context to be fully initialized
            await self._init_future

    async def stop(self) -> None:
        """Stop the background task and clean up resources."""
        if self._task and not self._task.done() and self._request_queue:
            self._running = False

            # Create a future for the stop command
            stop_future = asyncio.Future()
            await self._request_queue.put(("stop", None, stop_future))
            await stop_future
            await self._task

            # Clear state
            self._request_queue = None
            self._init_future = None
            self._session = None

    async def call_tool(self, **kwargs) -> str:
        """Call the codemcp tool in the subprocess."""
        if not self._running or not self._request_queue:
            await self.start()

        # Create a future for this specific request
        response_future = asyncio.Future()

        # Send the request and its associated future to the manager task
        if self._request_queue:  # Safety check
            await self._request_queue.put(("call", kwargs, response_future))
        else:
            response_future.set_exception(RuntimeError("Request queue not available"))

        # Wait for the response
        return await response_future

    async def _run_manager_task(
        self, request_queue: Queue, init_future: asyncio.Future
    ) -> None:
        """
        Background task that owns and manages the async context managers lifecycle.

        Parameters:
            request_queue: Queue to receive commands from
            init_future: Future to signal when initialization is complete
        """
        session = None
        running = True
        try:
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
                    # Store the session in self for monitoring/debugging
                    self._session = session
                    await session.initialize()

                    # Signal that initialization is complete
                    init_future.set_result(True)

                    # Process commands until told to stop
                    while running and self._running:
                        try:
                            command, args, future = await request_queue.get()

                            if command == "stop":
                                future.set_result(True)
                                running = False
                                break

                            if command == "call":
                                try:
                                    result = await session.call_tool(
                                        "codemcp", arguments=args
                                    )
                                    future.set_result(result)
                                except Exception as e:
                                    future.set_exception(e)

                        except Exception as e:
                            logging.error(
                                "Error in hot reload manager task", exc_info=True
                            )
                            if "future" in locals() and not future.done():
                                future.set_exception(e)

        except Exception as e:
            logging.error("Error initializing hot reload context", exc_info=True)
            if not init_future.done():
                init_future.set_exception(e)

        finally:
            # Resources are automatically cleaned up by async with blocks
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
