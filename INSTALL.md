If you haven't read it already, please check "Installation" section in
[README.md](README.md) for the **recommended** install methods.  This file
documents all of the legacy installation methods if you want to do it the hard
way.

## Configure codemcp in your Claude Desktop

### For macOS/Linux

Create or edit your `~/.config/anthropic/claude/claude_desktop_config.json` file and add the following:

```json
{
  "mcpServers": {
    "codemcp": {
      "command": "/Users/<USERNAME>/.local/bin/uvx",
      "args": [
        "--from",
        "git+https://github.com/ezyang/codemcp@prod",
        "codemcp"
      ]
    }
  }
}
```

### For Windows

Create or edit your `%USERPROFILE%\.anthropic\claude\claude_desktop_config.json` file and add the following:

```json
{
  "mcpServers": {
    "codemcp": {
      "command": "C:\\Users\\<USERNAME>\\.local\\bin\\uvx.exe",
      "args": [
        "--from",
        "git+https://github.com/ezyang/codemcp@prod",
        "codemcp"
      ]
    }
  }
}
```

### Using with WSL (recommended for Windows users)

If you're using Windows Subsystem for Linux, you can configure codemcp to run within your WSL environment. This is useful if you prefer developing in a Linux environment while on Windows.

Add the following configuration to your `claude_desktop_config.json` file:

```json
{
  "mcpServers": {
    "codemcp": {
      "command": "wsl.exe",
      "args": [
        "bash",
        "-c",
        "/home/NameOfWSLUser/.local/bin/uvx --from git+https://github.com/ezyang/codemcp@prod codemcp"
      ]
    }
  }
}
```

Replace `NameOfWSLUser` with your actual WSL username. This configuration runs the `uvx` command inside your WSL environment while allowing Claude Desktop to communicate with it.

This configuration comes with the added benefit of being able to access your Linux filesystem directly. When initializing codemcp in Claude Desktop, you can use a path to your WSL project like:

```
Initialize codemcp with /home/NameOfWSLUser/project_in_wsl_to_work_on
```

Make sure you have installed Python 3.12+ and uv within your WSL distribution. You might need to run the following commands in your WSL terminal:

```bash
# Install Python 3.12 (if not already installed)
sudo apt update
sudo apt install python3.12

# Install uv
curl -sSf https://astral.sh/uv/install.sh | sh
```

After configuring, restart Claude Desktop. The hammer icon should appear, indicating codemcp has loaded successfully.

Restart the Claude Desktop app after modifying the JSON.  If the MCP
successfully loaded, a hammer icon will appear and when you click it "codemcp"
will be visible.

### Global install with pip

If you don't want to use uv, you can also globally pip install the latest
codemcp version, assuming your global Python install is recent enough (Python
3.12) and doesn't have Python dependencies that conflict with codemcp.  Some
users report this is easier to get working on Windows.

1. `pip install git+https://github.com/ezyang/codemcp@prod`
2. Add the following configuration to `claude_desktop_config.json` file
```json
{
    "mcpServers": {
         "codemcp": {
               "command": "python",
               "args": ["-m", "codemcp"]
            }
    }
}
```
3. Restart Claude Desktop

You will need to manually upgrade codemcp to take updates using
`pip install --upgrade git+https://github.com/ezyang/codemcp@prod`

### Other tips

Pro tip: If the server fails to load, go to Settings > Developer > codemcp >
Logs to look at the MCP logs, they're very helpful for debugging. The logs on
Windows should be loaded `C:\Users\<user_name>\AppData\Roaming\Claude\logs`
(replace `<user_name>` with your username.

Pro tip: if on Windows, _**try using the [WSL instructions](#using-with-wsl-recommended-for-windows-users) instead**_, but if you insist on using Windows directly: if the logs say "Git executable not found. Ensure that
Git is installed and available", and you *just* installed Git, reboot your
machine (the PATH update hasn't propagated.)  If this still doesn't work, open
System Properties > Environment Variables > System variables > Path and ensure
there is an entry for Git.

Pro tip: if you like to live dangerously, you can change `prod` to `main`.  If
you want to pin to a specific release, replace it with `0.3.0` or similar.

Pro tip: it is supported to specify only `uvx` as the command, but uvx must be
in your global PATH (not just added via a shell profile); on OS X, this is
typically not the case if you used the self installer (unless you installed
into a system location like `/usr/local/bin`).
