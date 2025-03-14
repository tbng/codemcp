#!/usr/bin/env python3

import asyncio
import logging
import os
import subprocess
from typing import Dict, List, Optional


async def run_command(
    cmd: List[str],
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    check: bool = True,
    capture_output: bool = True,
    text: bool = True,
    wait_time: Optional[float] = None,  # Renamed from timeout to avoid ASYNC109
    shell: bool = False,
) -> subprocess.CompletedProcess:
    """
    Run a subprocess command with consistent logging asynchronously.

    Args:
        cmd: Command to run as a list of strings
        cwd: Current working directory for the command
        env: Environment variables to set for the command
        check: If True, raise CalledProcessError if the command returns non-zero exit code
        capture_output: If True, capture stdout and stderr
        text: If True, decode stdout and stderr as text
        wait_time: Timeout in seconds
        shell: If True, run command in a shell

    Returns:
        CompletedProcess instance with attributes args, returncode, stdout, stderr

    Raises:
        subprocess.CalledProcessError: If check=True and process returns non-zero exit code
        subprocess.TimeoutExpired: If the process times out
    """
    # Log the command being run at INFO level
    log_cmd = " ".join(str(c) for c in cmd)
    logging.info(f"Running command: {log_cmd}")

    # Only log suspicious git operations when debug is enabled
    if cmd and cmd[0] == "git" and os.environ.get("CODEMCP_DEBUG"):
        import inspect

        # Determine codemcp repo path dynamically
        module_file = inspect.getfile(run_command)
        current_module_dir = os.path.dirname(os.path.abspath(module_file))
        codemcp_repo_path = os.path.abspath(os.path.join(current_module_dir, ".."))

        # Check if we're operating in the codemcp repository
        specified_dir = os.path.abspath(cwd) if cwd else os.path.abspath(os.curdir)
        if specified_dir == codemcp_repo_path or specified_dir.startswith(
            codemcp_repo_path + os.sep
        ):
            logging.warning(
                f"Git command running in codemcp repository: {specified_dir}"
            )

    # Prepare stdout and stderr pipes
    stdout_pipe = asyncio.subprocess.PIPE if capture_output else None
    stderr_pipe = asyncio.subprocess.PIPE if capture_output else None

    # Run the subprocess asynchronously
    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        env=env,
        stdout=stdout_pipe,
        stderr=stderr_pipe,
    )

    try:
        # Wait for the process to complete with optional timeout
        stdout_data, stderr_data = await asyncio.wait_for(
            process.communicate(), timeout=wait_time
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        raise subprocess.TimeoutExpired(cmd, wait_time)

    # Handle text conversion
    stdout = ""
    stderr = ""
    if capture_output:
        if text and stdout_data:
            stdout = stdout_data.decode()
            logging.debug(f"Command stdout: {stdout}")
        elif stdout_data:
            stdout = stdout_data
            logging.debug(f"Command stdout: {len(stdout_data)} bytes")

        if text and stderr_data:
            stderr = stderr_data.decode()
            logging.debug(f"Command stderr: {stderr}")
        elif stderr_data:
            stderr = stderr_data
            logging.debug(f"Command stderr: {len(stderr_data)} bytes")

    # Log the return code
    returncode = process.returncode
    logging.debug(f"Command return code: {returncode}")

    # Create a CompletedProcess object to maintain compatibility
    result = subprocess.CompletedProcess(
        args=cmd, returncode=returncode, stdout=stdout, stderr=stderr
    )

    # Re-raise CalledProcessError if check is True and command failed
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, cmd, output=result.stdout, stderr=result.stderr
        )

    return result
