# DataSHIELD MCP

[![GitHub Actions](https://github.com/obiba/datashield-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/obiba/datashield-mcp/actions)

[DataSHIELD](https://datashield.org/) enables privacy-preserving federated analysis across distributed datasets, but researchers must learn specialized R commands and APIs. This creates a barrier to adoption, particularly for those less familiar with programming or DataSHIELD's specific syntax.

DataSHIELD MCP ([Model Context Protocol](https://modelcontextprotocol.io/)), is an open-source tool that allows researchers to interact with DataSHIELD infrastructure using natural language through AI agents, dramatically lowering the technical barrier to federated analysis.

DataSHIELD MCP is implemented as an MCP server in Python, integrating with the [datashield-python](https://github.com/datashield/datashield-python) package and an AI agent interface such as [OpenCode](https://opencode.ai/). It exposes 20+ DataSHIELD operations as structured tools, including server connection management, table/resource assignment, variable exploration (dimensions, summaries, frequencies), statistical analyses (correlation, GLM), and visualization (histograms). The system maintains session state and provides built-in [PICO methodology](https://en.wikipedia.org/wiki/PICO_process) guidance specific to federated analysis contexts.

Users can perform complex DataSHIELD workflows using conversational commands rather than code. For example, asking "connect to European cohorts, assign diabetes tables, and run logistic regression for physical activity and T2D diagnosis" automatically translates to the appropriate sequence of DataSHIELD operations. The tool handles harmonization feasibility checks, disclosure control awareness, and multi-node coordination transparently.

DataSHIELD MCP democratizes access to federated analysis by removing programming barriers while maintaining the privacy-preserving guarantees of DataSHIELD. This natural language interface makes federated research more accessible to epidemiologists, clinicians, and researchers who may lack extensive programming experience, potentially accelerating adoption and expanding DataSHIELD's impact.

## Installation

### Install MCP Tool

The Python project manager `uv` is required: see [uv documentation](https://docs.astral.sh/uv/).

Install the DataSHIELD MCP tool using `uv`:

```sh
uv tool install git+ssh://git@github.com/obiba/datashield-mcp
```

### DataSHIELD Configuration

You will also need to setup a DataSHIELD configuration. See the **Configuration** instructions at the [DataSHIELD Python package README](https://github.com/datashield/datashield-python/). 

## Usage

Use [OpenCode](https://opencode.ai/docs/), [Claude Code](https://claude.com/product/claude-code) or [Codex](https://developers.openai.com/codex/) as the AI agent prompt interface.

### From any folder

**OpenCode**

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

**Claude Code**

Project-scoped MCP configuration is stored in `.mcp.json`:

```json
{
  "mcpServers": {
    "datashield": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "datashield-mcp"]
    }
  }
}
```

And verify it is working:

```sh
claude mcp list
```

**Codex**

Register the MCP server in your user configuration `~/.codex/config.toml`:

```toml
[mcp_servers.datashield]
command = "datashield-mcp"
```

OR register it from the command line:

```sh
codex mcp add datashield -- datashield-mcp
```

And verify it is working:

```sh
codex mcp list
```

### From this project

**OpenCode**

Use OpenCode from this project folder: the DataSHIELD MCP server, behind the [guard](#guard-plan-enforcement), is declared in the `opencode.json` configuration file.

Verify that the MCP is operational:

```sh
opencode mcp list
```

Start OpenCode and list servers available, open connection, assign tables etc.:

```sh
opencode
```

**Claude Code**

Use Claude Code from this project folder: the DataSHIELD MCP server, behind the [guard](#guard-plan-enforcement), is declared in the `.mcp.json` configuration file.

Verify that the MCP is operational:

```sh
claude mcp list
```

Start Claude Code and list servers available:

```sh
claude
```

**Codex**

Use Codex from this project folder: the DataSHIELD MCP server, behind the [guard](#guard-plan-enforcement), is declared in the `.codex/config.toml` configuration file (project-scoped configuration is only loaded for trusted projects, so accept the trust prompt when Codex starts).

Verify that the MCP is operational:

```sh
codex mcp list
```

Start Codex and list servers available:

```sh
codex
```

## Guard (plan enforcement)

`datashield-guard` is an MCP proxy in front of the DataSHIELD MCP server that adds client-side controls on top of the server-side DataSHIELD disclosure settings:

* **Plan then execute**: data tools are denied until the model submits an analysis plan (`submit_plan`: research question, tables, variables, subsets, tools) and a human approves it. Each call is then checked against the plan.
* **Attack patterns**: identifier-like variables, free-form expressions (only allowlisted functions and planned names), row slicing, near-overlapping subsets (differencing), long subset chains (progressive narrowing), rate limit and repeated identical queries.
* **Audit**: append-only JSON lines in `.datashield/audit/<session>.jsonl` (plan, calls, denials, results).

The project configurations (`.mcp.json`, `.codex/config.toml`, `opencode.json`) declare the guard *instead of* the DataSHIELD MCP server, so that the model cannot bypass it (by default it runs the DataSHIELD MCP server in-process, or use `--upstream <url>`):

```json
{
  "mcpServers": {
    "datashield": { "type": "stdio", "command": "uv", "args": ["run", "datashield-guard", "serve"] }
  }
}
```

Review and approve submitted plans from a terminal:

```sh
uv run datashield-guard list
uv run datashield-guard approve <plan_id>
```

The approval is out of the model's reach only if the model has no shell access: in Claude Code/Codex, do not allow it to run `datashield-guard` nor to edit `.datashield/`.

## Development

Install the dependencies with:

```sh
make install
```

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

Then configure your AI assistant to connect to this remote server (note: this bypasses the guard).

**Claude Code**

Replace the stdio declaration in `.mcp.json` with an HTTP one:

```json
{
  "mcpServers": {
    "datashield": {
      "type": "http",
      "url": "http://127.0.0.1:8008/mcp"
    }
  }
}
```

OR register it from the command line (use `--scope project` to write it to `.mcp.json` instead of your user config):

```sh
claude mcp add --transport http datashield http://127.0.0.1:8008/mcp
```

Verify the connection with `claude mcp list` (or `/mcp` inside a Claude Code session).

**OpenCode**

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

**Codex**

Replace the stdio declaration in `.codex/config.toml` (or `~/.codex/config.toml`) with an HTTP one:

```toml
[mcp_servers.datashield]
url = "http://127.0.0.1:8008/mcp"
```

OR register it from the command line:

```sh
codex mcp add datashield --url http://127.0.0.1:8008/mcp
```

Verify the connection with `codex mcp list` (or `/mcp` inside a Codex session).
