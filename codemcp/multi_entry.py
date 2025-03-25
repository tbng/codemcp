#!/usr/bin/env python3
from mcp.server.fastmcp import Context, FastMCP

from codemcp.tools.edit_file import edit_file_content
from codemcp.tools.grep import grep_files
from codemcp.tools.init_project import init_project
from codemcp.tools.ls import ls_directory
from codemcp.tools.read_file import read_file_content
from codemcp.tools.write_file import write_file_content

mcp = FastMCP("codemcp_multi")


# Helper function to get a chat_id from a Context
def get_chat_id_from_context(ctx: Context) -> str:
    # Generate a chat_id from the context
    ctx_id = getattr(ctx, "id", None)
    return f"multi-{ctx_id}" if ctx_id else "multi-default"


@mcp.tool()
async def read_file(
    ctx: Context, file_path: str, offset: int | None = None, limit: int | None = None
) -> str:
    # Get chat ID from context
    chat_id = get_chat_id_from_context(ctx)
    return await read_file_content(file_path, offset, limit, chat_id)


@mcp.tool()
async def write_file(
    ctx: Context, file_path: str, content: str, description: str
) -> str:
    # Get chat ID from context
    chat_id = get_chat_id_from_context(ctx)
    return await write_file_content(file_path, content, description, chat_id)


@mcp.tool()
async def edit_file(
    ctx: Context, file_path: str, old_string: str, new_string: str, description: str
) -> str:
    # Get chat ID from context
    chat_id = get_chat_id_from_context(ctx)
    return await edit_file_content(
        file_path, old_string, new_string, None, description, chat_id
    )


@mcp.tool()
async def ls(ctx: Context, file_path: str) -> str:
    # Get chat ID from context
    chat_id = get_chat_id_from_context(ctx)
    return await ls_directory(file_path, chat_id)


@mcp.tool()
async def grep(
    ctx: Context, pattern: str, path: str | None = None, include: str | None = None
) -> str:
    # Get chat ID from context
    chat_id = get_chat_id_from_context(ctx)
    result = await grep_files(pattern, path, include, chat_id)
    return result.get(
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
    # The init_project function actually doesn't accept a chat_id parameter
    # It generates its own chat_id, so we don't pass it as an argument
    return await init_project(file_path, user_prompt, subject_line, reuse_head_chat_id)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
