#!/usr/bin/env python3

import asyncio
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_serve_command():
    """Test that the serve command starts correctly."""
    # Start the server process
    process = subprocess.Popen(
        [sys.executable, "-m", "codemcp", "serve", "--port", "8765"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Give the server time to start
    await asyncio.sleep(2)

    try:
        # Test that the server process is still running (hasn't crashed)
        assert process.poll() is None

        # Check that something was written to stdout
        out, err = process.stdout.readline(), process.stderr.readline()
        assert out or err, "Expected some output from server"
    finally:
        # Ensure the server is shut down
        if sys.platform == "win32":
            process.send_signal(signal.CTRL_C_EVENT)
        else:
            process.send_signal(signal.SIGTERM)

        # Give it time to shut down
        await asyncio.sleep(1)

        # Force kill if still running
        if process.poll() is None:
            process.kill()
