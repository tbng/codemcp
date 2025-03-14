#!/usr/bin/env python3
from mcp.server.fastmcp import Context, FastMCP

from codemcp.tools.edit_file import edit_file_content
from codemcp.tools.grep import grep_files
from codemcp.tools.init_project import init_project
from codemcp.tools.ls import ls_directory
from codemcp.tools.read_file import read_file_content
from codemcp.tools.write_file import write_file_content

mcp = FastMCP("codemcp_multi")


@mcp.tool()
async def read_file(
    ctx: Context, file_path: str, offset: int = None, limit: int = None
) -> str:
    return await read_file_content(file_path, offset, limit)


@mcp.tool()
async def write_file(
    ctx: Context, file_path: str, content: str, description: str
) -> str:
    return await write_file_content(file_path, content, description)


@mcp.tool()
async def edit_file(
    ctx: Context, file_path: str, old_string: str, new_string: str, description: str
) -> str:
    return await edit_file_content(file_path, old_string, new_string, None, description)


@mcp.tool()
async def ls(ctx: Context, file_path: str) -> str:
    return await ls_directory(file_path)


@mcp.tool()
async def grep(
    ctx: Context, pattern: str, path: str = None, include: str = None
) -> str:
    result = grep_files(pattern, path, include)
    return await result.get(
        "resultForAssistant", f"Found {result.get('numFiles', 0)} file(s)"
    )


@mcp.tool()
async def init_project_tool(
    ctx: Context,
    file_path: str,
    user_prompt: str,
    subject_line: str,
    reuse_head_chat_id: bool = False,
) -> str:
    return await init_project(file_path, user_prompt, subject_line, reuse_head_chat_id)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
