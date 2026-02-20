from collections.abc import AsyncIterator
import uuid
import random
import io
import urllib.parse
import base64

from contextlib import asynccontextmanager
from pathlib import Path
from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ImageContent, TextContent
from mcp.server.session import ServerSession
from datashield import DSConfig, DSSession, DSLoginBuilder
import matplotlib
from datashield_mcp.models import AppContext, DSContext
from datashield_mcp.logging import logger

matplotlib.use("Agg")  # must be before importing pyplot
import matplotlib.pyplot as plt


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
        for session_id, dscontext in context.sessions.items():
            logger.info(f"Closing DataSHIELD session {session_id}.")
            try:
                dscontext.session.close()
                # TODO - add more cleanup if needed (e.g. remove temporary files)
            except Exception:
                logger.warning(f"Failed to close DataSHIELD session {session_id}.")
        logger.info("FastMCP server shutdown complete.")


# Create an MCP server
mcp = FastMCP("DataSHIELD", json_response=True, lifespan=app_lifespan)


@mcp.tool()
def available_servers(ctx: Context[ServerSession, AppContext]) -> list[str]:
    """List available DataSHIELD servers

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
    Returns:
        A list of DataSHIELD server names available for connection
    """
    config = DSConfig.load()
    names = [s.name for s in config.servers]
    logger.info(f"Available DataSHIELD servers: {names}")
    return names


@mcp.tool()
def open(ctx: Context[ServerSession, AppContext], server_names: list[str]) -> dict[str, str | list[str]]:
    """Open a DataSHIELD session
    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        server_names: A list of server names to connect to
    Returns:
        The session ID for the connected session and the list of servers that were successfully connected to
    Raises:
        ValueError: If the connection to the specified servers fails
    """
    logins = DSLoginBuilder(names=server_names).build()
    session = DSSession(logins)
    session.open()
    logger.info(f"Opened DataSHIELD session with servers: {session.get_connection_names()} / {server_names}")
    # store the session for later use
    session_id = str(uuid.uuid4())
    ctx.request_context.lifespan_context.sessions[session_id] = DSContext(session=session)
    logger.info(f"[{session_id}] Session stored in application context.")
    return {"session_id": session_id, "servers": session.get_connection_names()}


@mcp.tool()
def close(ctx: Context[ServerSession, AppContext], session_id: str) -> None:
    """Close a DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if dscontext and dscontext.session:
        logger.info(f"[{session_id}] Closing DataSHIELD session.")
        dscontext.session.close()
        del ctx.request_context.lifespan_context.sessions[session_id]


@mcp.tool()
def list_tables(ctx: Context[ServerSession, AppContext], session_id: str) -> dict[str, list[str]]:
    """List tables available in the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
    Returns:
        A dictionary mapping server names to lists of available tables
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    tables = dscontext.session.tables()
    logger.info(f"[{session_id}] Available tables: {tables}")
    return tables


@mcp.tool()
def list_resources(ctx: Context[ServerSession, AppContext], session_id: str) -> dict[str, list[str]]:
    """List resources available in the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
    Returns:
        A dictionary mapping server names to lists of available resources
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    resources = dscontext.session.resources()
    logger.info(f"[{session_id}] Available resources: {resources}")
    return resources


@mcp.tool()
def list_symbols(ctx: Context[ServerSession, AppContext], session_id: str) -> dict[str, list[str]]:
    """List symbols available in the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
    Returns:
        A dictionary mapping server names to lists of available symbols in the remote R sessions
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    symbols = dscontext.session.ls()
    logger.info(f"[{session_id}] Available symbols: {symbols}")
    return symbols


@mcp.tool()
def remove_symbols(
    ctx: Context[ServerSession, AppContext], session_id: str, symbols: list[str]
) -> dict[str, list[str]]:
    """Remove symbols from the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        symbols: A list of symbol names to remove from the remote R sessions
    Returns:
        A dictionary mapping server names to lists of available symbols after removal
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    for symbol in symbols:
        dscontext.session.rm(symbol)
    symbols = dscontext.session.ls()
    logger.info(f"[{session_id}] Available symbols after removal: {symbols}")
    return symbols


@mcp.tool()
def assign_tables(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    symbol: str,
    tables: dict[str, str],
) -> dict[str, list[str]]:
    """Assign tables to the connected DataSHIELD session
    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        symbol: The symbol name to assign the tables to in the remote R sessions
        tables: A dictionary mapping server names to table names to assign to the symbol
    Returns:
        A dictionary mapping server names to lists of available symbols after assignment
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    dscontext.session.assign_table(symbol, tables=tables)
    symbols = dscontext.session.ls()
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
    """Assign resources to the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        symbol: The symbol name to assign the resources to in the remote R sessions
        resources: A dictionary mapping server names to resource names to assign to the symbol
        as_data_frame: Whether to assign the resources as data frames (True) or as resource objects (False) in the remote R sessions
    Returns:
        A dictionary mapping server names to lists of available symbols after assignment
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    res_symbol = f"{symbol}_res"
    dscontext.session.assign_resource(res_symbol, resources=resources)
    if as_data_frame:
        dscontext.session.assign_expr(symbol, f"as.resource.data.frame({res_symbol}, strict=TRUE)")
    else:
        dscontext.session.assign_expr(symbol, f"as.resource.object({res_symbol})")
    symbols = dscontext.session.ls()
    logger.info(f"[{session_id}] Assigned resources to symbol '{symbol}'. Current symbols: {symbols}")
    return symbols


@mcp.tool()
def list_colnames(ctx: Context[ServerSession, AppContext], session_id: str, symbol: str) -> dict[str, list[str]]:
    """List column names of a table in the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        symbol: The symbol name of the table to list column names for in the remote R sessions
    Returns:
        A dictionary mapping server names to lists of column names for the specified symbol in the remote R sessions
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    colnames = dscontext.session.aggregate(f"colnamesDS('{symbol}')")
    logger.info(f"[{session_id}] Column names for symbol '{symbol}': {colnames}")
    return colnames


@mcp.tool()
def get_class(ctx: Context[ServerSession, AppContext], session_id: str, symbol: str) -> dict[str, str]:
    """Get the class of a symbol in the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        symbol: The symbol name to get the class of in the remote R sessions
    Returns:
        A dictionary mapping server names to the class of the specified symbol in the remote R sessions
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    classes = dscontext.session.aggregate(f"classDS('{symbol}')")
    logger.info(f"[{session_id}] Class for symbol '{symbol}': {classes}")
    return classes


@mcp.tool()
def get_mean(
    ctx: Context[ServerSession, AppContext], session_id: str, symbol: str
) -> dict[str, dict[str, float | str]]:
    """Get the mean of a symbol in the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        symbol: The symbol name to get the mean of in the remote R sessions
    Returns:
        A dictionary mapping server names to the mean value of the specified symbol in the remote R sessions
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    means = dscontext.session.aggregate(f"meanDS({symbol})")
    logger.info(f"[{session_id}] Mean for symbol '{symbol}': {means}")
    return means


@mcp.tool()
def get_histogram(
    ctx: Context[ServerSession, AppContext], session_id: str, symbol: str
) -> list[TextContent | ImageContent]:
    """Get the histogram of a symbol in the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        symbol: The symbol name to get the histogram of in the remote R sessions
    Returns:
        A list of TextContent and ImageContent objects containing the histogram information and image for the specified symbol in the remote R sessions
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    data = dscontext.session.aggregate(
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

    image_url = f"plot://{session_id}/histogram_{safe_symbol}"

    return [
        TextContent(
            type="text",
            text=f"Histogram of {symbol} saved to {output_path} (url is {image_url})",
        ),
        ImageContent(type="image", data=image_b64, mimeType="image/png"),
    ]


# FIXME - make it a tool instead?
@mcp.resource("plot://{name}", mime_type="image/png")
def get_plot(name: str) -> bytes:
    """Get a saved plot
    Args:
        name: The name of the plot to retrieve (should match the filename used when saving the plot, e.g. 'histogram_symbol')
    Returns:
        The bytes of the saved plot image
    Raises:
        FileNotFoundError: If the specified plot does not exist
        ValueError: If the plot name is invalid (e.g. contains path traversal characters)
    """
    work_dir = Path.cwd() / ".datashield" / "work"
    # url decode name
    name = urllib.parse.unquote(name)
    filename = f"{name}.png"
    file_path = work_dir / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Plot '{name}' not found")
    # Make sure it is not a relative path that could escape the work directory
    if not file_path.resolve().is_relative_to(work_dir.resolve()):
        raise ValueError("Invalid plot name")
    return file_path.read_bytes()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
