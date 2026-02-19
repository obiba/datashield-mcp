from collections.abc import AsyncIterator
import sys
import uuid
import logging
import random
import io

import base64
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ImageContent, TextContent
from mcp.server.session import ServerSession
from datashield import DSConfig, DSSession, DSLoginBuilder
import matplotlib

matplotlib.use("Agg")  # must be before importing pyplot
import matplotlib.pyplot as plt

# Create log directory if it doesn't exist
# Try current folder first, fall back to home if not writable
log_dir = Path.cwd() / ".datashield" / "logs"
try:
    log_dir.mkdir(parents=True, exist_ok=True)
except (PermissionError, OSError):
    log_dir = Path.home() / ".datashield" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

# Configure logging to file and stderr
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "mcp.log"),
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Application context with typed dependencies."""

    sessions: dict[str, DSSession]


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Lifespan context manager for the FastMCP server."""
    # Initialize application context
    context = AppContext(sessions={})
    logger.info("Starting FastMCP server with DataSHIELD integration.")
    try:
        yield context
    finally:
        # Clean up resources on shutdown
        for session_id, session in context.sessions.items():
            logger.info(f"Closing DataSHIELD session {session_id}.")
            try:
                session.close()
            except Exception:
                logger.warning(f"Failed to close DataSHIELD session {session_id}.")
        logger.info("FastMCP server shutdown complete.")


# Create an MCP server
mcp = FastMCP("DataSHIELD", json_response=True, lifespan=app_lifespan)


@mcp.tool()
def available_servers(ctx: Context[ServerSession, AppContext]) -> list[str]:
    """List available DataSHIELD servers"""
    # For demonstration, we return a static list of server names
    # In a real implementation, this could query a configuration or discovery service
    config = DSConfig.load()
    names = [s.name for s in config.servers]
    logger.info(f"Available DataSHIELD servers: {names}")
    return names


@mcp.tool()
def open(ctx: Context[ServerSession, AppContext], server_names: list[str]) -> dict[str, str | list[str]]:
    """Open a DataSHIELD session
    Args:
        server_names: A list of server names to connect to
    Returns:
        The session ID for the connected session
    """
    logins = DSLoginBuilder(names=server_names).build()
    session = DSSession(logins)
    session.open()
    logger.info(f"Opened DataSHIELD session with servers: {session.get_connection_names()} / {server_names}")
    # store the session for later use
    session_id = str(uuid.uuid4())
    ctx.request_context.lifespan_context.sessions[session_id] = session
    logger.info(f"[{session_id}] Session stored in application context.")
    return {"session_id": session_id, "servers": session.get_connection_names()}


@mcp.tool()
def close(ctx: Context[ServerSession, AppContext], session_id: str) -> None:
    """Close a DataSHIELD session"""
    session = ctx.request_context.lifespan_context.sessions.get(session_id)
    if session:
        logger.info(f"[{session_id}] Closing DataSHIELD session.")
        session.close()
        del ctx.request_context.lifespan_context.sessions[session_id]


@mcp.tool()
def list_tables(ctx: Context[ServerSession, AppContext], session_id: str) -> dict[str, list[str]]:
    """List tables available in the connected DataSHIELD session"""
    session = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not session:
        raise ValueError("Not connected to DataSHIELD")
    tables = session.tables()
    logger.info(f"[{session_id}] Available tables: {tables}")
    return tables


@mcp.tool()
def list_resources(ctx: Context[ServerSession, AppContext], session_id: str) -> dict[str, list[str]]:
    """List resources available in the connected DataSHIELD session"""
    session = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not session:
        raise ValueError("Not connected to DataSHIELD")
    resources = session.resources()
    logger.info(f"[{session_id}] Available resources: {resources}")
    return resources


@mcp.tool()
def list_symbols(ctx: Context[ServerSession, AppContext], session_id: str) -> dict[str, list[str]]:
    """List symbols available in the connected DataSHIELD session"""
    session = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not session:
        raise ValueError("Not connected to DataSHIELD")
    symbols = session.ls()
    logger.info(f"[{session_id}] Available symbols: {symbols}")
    return symbols


@mcp.tool()
def remove_symbols(
    ctx: Context[ServerSession, AppContext], session_id: str, symbols: list[str]
) -> dict[str, list[str]]:
    """Remove symbols from the connected DataSHIELD session"""
    session = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not session:
        raise ValueError("Not connected to DataSHIELD")
    for symbol in symbols:
        session.rm(symbol)
    symbols = session.ls()
    logger.info(f"[{session_id}] Available symbols after removal: {symbols}")
    return symbols


@mcp.tool()
def assign_tables(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    symbol: str,
    tables: dict[str, str],
) -> dict[str, list[str]]:
    """Assign tables to the connected DataSHIELD session"""
    session = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not session:
        raise ValueError("Not connected to DataSHIELD")
    session.assign_table(symbol, tables=tables)
    symbols = session.ls()
    logger.info(f"[{session_id}] Assigned tables to symbol '{symbol}'. Current symbols: {symbols}")
    return symbols


@mcp.tool()
def assign_resources(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    symbol: str,
    resources: dict[str, str],
    as_data_frame: bool = True,
) -> dict[str, list[str]]:
    """Assign resources to the connected DataSHIELD session"""
    session = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not session:
        raise ValueError("Not connected to DataSHIELD")
    res_symbol = f"{symbol}_res"
    session.assign_resource(res_symbol, resources=resources)
    if as_data_frame:
        session.assign_expr(symbol, f"as.resource.data.frame({res_symbol}, strict=TRUE)")
    else:
        session.assign_expr(symbol, f"as.resource.object({res_symbol})")
    symbols = session.ls()
    logger.info(f"[{session_id}] Assigned resources to symbol '{symbol}'. Current symbols: {symbols}")
    return symbols


@mcp.tool()
def list_colnames(ctx: Context[ServerSession, AppContext], session_id: str, symbol: str) -> dict[str, list[str]]:
    """List column names of a table in the connected DataSHIELD session"""
    session = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not session:
        raise ValueError("Not connected to DataSHIELD")
    colnames = session.aggregate(f"colnamesDS('{symbol}')")
    logger.info(f"[{session_id}] Column names for symbol '{symbol}': {colnames}")
    return colnames


@mcp.tool()
def get_class(ctx: Context[ServerSession, AppContext], session_id: str, symbol: str) -> dict[str, str]:
    """Get the class of a symbol in the connected DataSHIELD session"""
    session = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not session:
        raise ValueError("Not connected to DataSHIELD")
    classes = session.aggregate(f"classDS('{symbol}')")
    logger.info(f"[{session_id}] Class for symbol '{symbol}': {classes}")
    return classes


@mcp.tool()
def get_mean(
    ctx: Context[ServerSession, AppContext], session_id: str, symbol: str
) -> dict[str, dict[str, float | str]]:
    """Get the mean of a symbol in the connected DataSHIELD session"""
    session = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not session:
        raise ValueError("Not connected to DataSHIELD")
    means = session.aggregate(f"meanDS({symbol})")
    logger.info(f"[{session_id}] Mean for symbol '{symbol}': {means}")
    return means


@mcp.tool()
def get_histogram(
    ctx: Context[ServerSession, AppContext], session_id: str, symbol: str
) -> list[TextContent | ImageContent]:
    """Get the histogram of a symbol in the connected DataSHIELD session"""
    session = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not session:
        raise ValueError("Not connected to DataSHIELD")
    data = session.aggregate(
        f"histogramDS2({symbol}, num.breaks=20, min=0, max=20, method.indicator=1, k=3, noise=0.25)"
    )
    fig, ax = plt.subplots()
    for server, hist in data.items():
        logger.info(f"[{session_id}] Histogram for symbol '{symbol}' on server '{server}': {hist}")
        breaks = hist["value"][0]["value"][0]["value"]
        counts = hist["value"][0]["value"][1]["value"]
        # random color
        color = (random.random(), random.random(), random.random(), 0.5)
        ax.bar(breaks[1:], counts, width=1, edgecolor="black", linewidth=0.5, alpha=0.5, label=server, color=color)
    ax.set_xlabel("Value")
    ax.set_ylabel("Frequency")
    ax.set_title(f"Histogram of {symbol}")
    ax.legend()

    # Save to file in .datashield/work/<session_id>
    work_dir = Path.cwd() / ".datashield" / "work" / session_id
    work_dir.mkdir(parents=True, exist_ok=True)
    # Generate filename from symbol (replace special chars)
    safe_symbol = symbol.replace("$", "_").replace("/", "_").replace("\\", "_")
    output_path = work_dir / f"histogram_{safe_symbol}.png"
    fig.savefig(output_path, format="png", bbox_inches="tight")
    logger.info(f"[{session_id}] Saved histogram to {output_path}")

    # Save to bytes buffer
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)  # important — avoid memory leaks
    buf.seek(0)
    image_b64 = base64.b64encode(buf.read()).decode("utf-8")

    return [
        TextContent(
            type="text",
            text=f"Histogram of {symbol} saved to {output_path}",
        ),
        ImageContent(type="image", data=image_b64, mimeType="image/png"),
    ]


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


# Add a prompt
@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
