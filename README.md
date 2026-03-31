# DataSHIELD MCP

A [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server to interact with a DataSHIELD infrastructure using natural language.

## Installation

### Dependencies

The Python project manager `uv` is required: see [uv documentation](https://docs.astral.sh/uv/).

Install the dependencies with:

```sh
make install
```

### Configuration

You will also need to setup a DataSHIELD configuration. See the **Configuration** instructions at the [DataSHIELD Python package README](https://github.com/datashield/datashield-python/). 

## Usage

Use [OpenCode](https://opencode.ai/docs/) as the AI agent prompt interface.

### From any folder

Install the DataSHIELD MCP tool using `uv`:

```sh
uv tool install git+ssh://git@github.com/obiba/datashield-mcp
```

Set up the `opencode.json` as follows:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "datashield": {
      "type": "local",
      "command": ["datashield-mcp"],
      "enabled": true
    }
  }
}
```

And verify it is working:

```sh
opencode mcp list
```

### From this project

Use OpenCode from this project folder: the DataSHIELD MCP server is declared in the `opencode.json` configuration file.

Verify that the MCP is operational:

```sh
opencode mcp list
```

Start OpenCode and list servers available, open connection, assign tables etc.:

```sh
opencode
```

## Development

### Built-in web interface

Start the MCP server manually:

```sh
make run-dev
```

Then go to http://localhost:6274/ and play with the web interface.

### Debugging

Start the MCP server as a stand-alone HTTP server:

```sh
make run-http
```

OR start it from the VSCode launcher with the configuration:

```json
  ...
  "configurations": [
    {
      "name": "Debug MCP Server",
      "type": "debugpy",
      "request": "launch",
      "module": "datashield_mcp.server",
      "args": ["--transport", "streamable-http"],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
  ...
```

Then configure OpenCode to connect to this remote server:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "datashield": {
      "type": "remote",
      "url": "http://127.0.0.1:8008/mcp",
      "enabled": true
    }
  }
}
```
