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

Use [OpenCode](https://opencode.ai/docs/) from this project folder: the DataSHIELD MCP server is declared in the `opencode.json` configuration file.

Verify that the MCP is operational:

```sh
opencode mcp list
```

Start OpenCode and list servers available, open connection, assign tables etc.:

```sh
opencode
```

## Development

Start the MCP server manually:

```sh
make run-dev
```

Then go to http://localhost:6274/ and play with the web interface.