#!/usr/bin/env python3

"""Test for init_project with codemcp/CHAT_ID reference."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from codemcp.git import get_codemcp_ref_message
from codemcp.shell import run_command
from codemcp.tools.init_project import init_project


@pytest.fixture
async def git_repo():
    """Create a temporary Git repository."""
    with tempfile.TemporaryDirectory() as tempdir:
        # Initialize git repo
        await run_command(
            ["git", "init"],
            cwd=tempdir,
            capture_output=True,
            text=True,
            check=True,
        )

        # Configure git user
        await run_command(
            ["git", "config", "user.name", "Test User"],
            cwd=tempdir,
            capture_output=True,
            text=True,
            check=True,
        )
        await run_command(
            ["git", "config", "user.email", "test@example.com"],
            cwd=tempdir,
            capture_output=True,
            text=True,
            check=True,
        )

        # Create a test file and commit it
        test_file = os.path.join(tempdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Test content")

        await run_command(
            ["git", "add", "test.txt"],
            cwd=tempdir,
            capture_output=True,
            text=True,
            check=True,
        )
        await run_command(
            ["git", "commit", "-m", "Initial commit"],
            cwd=tempdir,
            capture_output=True,
            text=True,
            check=True,
        )

        yield tempdir


async def test_init_project_uses_chat_ref(git_repo):
    """Test that init_project uses codemcp/CHAT_ID ref without advancing HEAD."""
    # Get the initial HEAD commit
    head_before = await run_command(
        ["git", "rev-parse", "HEAD"],
        cwd=git_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    initial_head = head_before.stdout.strip()

    # Call init_project with a subject line and user prompt
    subject_line = "feat: test subject"
    user_prompt = "This is a test prompt"
    result = await init_project(git_repo, user_prompt, subject_line)

    # Verify that HEAD hasn't changed
    head_after = await run_command(
        ["git", "rev-parse", "HEAD"],
        cwd=git_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    current_head = head_after.stdout.strip()
    assert initial_head == current_head, "HEAD should not have moved"

    # Extract the chat ID from the result
    chat_id_line = next(
        (line for line in result.splitlines() if "chat ID:" in line), None
    )
    assert chat_id_line is not None, "Chat ID not found in result"
    chat_id = chat_id_line.split(":", 1)[1].strip()

    # Verify that codemcp/CHAT_ID ref exists
    ref_exists = await run_command(
        ["git", "show-ref", f"codemcp/{chat_id}"],
        cwd=git_repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert ref_exists.returncode == 0, f"codemcp/{chat_id} ref should exist"

    # Get the commit message from the ref
    ref_message = await get_codemcp_ref_message(git_repo, chat_id)
    assert ref_message is not None, "Should be able to get message from ref"

    # Verify message contents
    assert subject_line in ref_message, "Subject line should be in the message"
    assert user_prompt in ref_message, "User prompt should be in the message"
    assert f"codemcp-id: {chat_id}" in ref_message, "Chat ID should be in the message"


async def test_commit_uses_ref_message(git_repo):
    """Test that when committing with a new chat ID, it uses the message from the ref."""
    # Initialize project with a subject line and user prompt
    subject_line = "feat: test subject"
    user_prompt = "This is a test prompt"
    result = await init_project(git_repo, user_prompt, subject_line)

    # Extract the chat ID from the result
    chat_id_line = next(
        (line for line in result.splitlines() if "chat ID:" in line), None
    )
    assert chat_id_line is not None, "Chat ID not found in result"
    chat_id = chat_id_line.split(":", 1)[1].strip()

    # Create a new file and commit it
    test_file = os.path.join(git_repo, "new_file.txt")
    with open(test_file, "w") as f:
        f.write("New file content")

    # Add the file
    await run_command(
        ["git", "add", "new_file.txt"],
        cwd=git_repo,
        capture_output=True,
        text=True,
        check=True,
    )

    # Import the commit_changes function
    from codemcp.git import commit_changes

    # Commit the changes
    success, message = await commit_changes(
        git_repo,
        "Added new file",
        chat_id=chat_id,
    )
    assert success, f"Commit should succeed, but got: {message}"

    # Get the commit message
    commit_message = await run_command(
        ["git", "log", "-1", "--pretty=%B"],
        cwd=git_repo,
        capture_output=True,
        text=True,
        check=True,
    )

    # Verify that the commit message includes both the original message and the new description
    assert subject_line in commit_message.stdout, (
        "Subject line should be in the commit message"
    )
    assert "Added new file" in commit_message.stdout, (
        "New description should be in the commit message"
    )
    assert f"codemcp-id: {chat_id}" in commit_message.stdout, (
        "Chat ID should be in the commit message"
    )
