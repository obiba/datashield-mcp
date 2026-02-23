from collections.abc import AsyncIterator
import uuid
import urllib.parse
from typing import Any

from contextlib import asynccontextmanager
from pathlib import Path
from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ImageContent, TextContent
from mcp.server.session import ServerSession
from datashield import DSConfig, DSSession, DSLoginBuilder
from datashield_mcp.models import AppContext, DSContext
from datashield_mcp.logs import logger
from datashield_mcp.clients.base import BaseClient


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

PICO_METHODOLOGY_PATH = Path(__file__).parent / "docs" / "datashield-pico.md"


@mcp.prompt()
def pico_methodology() -> str:
    """PICO methodology guide for DataSHIELD analysis."""
    return PICO_METHODOLOGY_PATH.read_text()


@mcp.tool()
def get_analysis_methodology() -> str:
    """
    Returns the recommended methodology for conducting a DataSHIELD analysis.
    Call this at the start of any analysis session to understand the PICO framework
    and the correct sequence of operations.
    """
    return PICO_METHODOLOGY_PATH.read_text()


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
    ctx.request_context.lifespan_context.sessions[session_id] = DSContext(id=session_id, session=session)
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
def list_table_variables(
    ctx: Context[ServerSession, AppContext], session_id: str, tables: dict[str, str]
) -> dict[str, list[dict]]:
    """List variables in a table available in the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        tables: A dictionary mapping server names to table names to list variables for
    Returns:
        A dictionary mapping server names to lists of available variables in the specified table
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD, or if the specified table does not exist
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    variables = dscontext.session.variables(tables=tables)
    logger.info(f"[{session_id}] Available variables in table: {variables}")
    return variables


@mcp.tool()
def list_taxonomies(ctx: Context[ServerSession, AppContext], session_id: str) -> dict[str, list[dict]]:
    """List taxonomies available in the connected DataSHIELD session. A taxonomy is a hierarchical structure of vocabulary
    terms that can be used to annotate variables in the data repository.
    Depending on the data repository's capabilities, taxonomies can be used to perform structured
    queries when searching for variables.

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
    Returns:
        A dictionary mapping server names to lists of available taxonomies
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    taxonomies = dscontext.session.taxonomies()
    logger.info(f"[{session_id}] Available taxonomies: {taxonomies}")
    return taxonomies


@mcp.tool()
def search_variables(ctx: Context[ServerSession, AppContext], session_id: str, query: str) -> dict[str, dict]:
    """Search for variables in the connected DataSHIELD session using a query string and an optional taxonomy filter

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        query: The search query string to use when searching for variables in the form of a simple keyword search or a
        more complex query using taxonomy based terms (e.g. <taxonomy>-<vocabulary>:"<term>"), with logicals (AND, OR) and
        parentheses for grouping.
    Returns:
        A dictionary mapping server names to the search results for variables that match the query and taxonomy filter
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD, or if the specified taxonomy does not exist
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    variables = dscontext.session.search_variables(query=query)
    logger.info(f"[{session_id}] Search results for query '{query}': {variables}")
    return variables


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
    remaining_symbols = dscontext.session.ls()
    logger.info(f"[{session_id}] Available symbols after removal: {remaining_symbols}")
    return remaining_symbols


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
def get_classes(ctx: Context[ServerSession, AppContext], session_id: str, symbol: str) -> dict[str, list[str]]:
    """Get the classes of a symbol in the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        symbol: The symbol name to get the classes of in the remote R sessions
    Returns:
        A dictionary mapping server names to the classes of the specified symbol in the remote R sessions
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    return BaseClient(dscontext).get_classes(symbol)


@mcp.tool()
def get_length(ctx: Context[ServerSession, AppContext], session_id: str, symbol: str) -> dict[str, int]:
    """Get the length of a symbol in the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        symbol: The symbol name to get the length of in the remote R sessions
    Returns:
        A dictionary mapping server names to the length of the specified symbol in the remote R sessions
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    return BaseClient(dscontext).get_length(symbol)


@mcp.tool()
def get_levels(ctx: Context[ServerSession, AppContext], session_id: str, symbol: str) -> dict[str, list[str]]:
    """Get the levels of a factor symbol in the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        symbol: The symbol name to get the levels of in the remote R sessions
    Returns:
        A dictionary mapping server names to the levels of the specified factor symbol in the remote R sessions
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    return BaseClient(dscontext).get_levels(symbol)


@mcp.tool()
def get_dimensions(ctx: Context[ServerSession, AppContext], session_id: str, symbol: str) -> dict[str, list[int]]:
    """Get the dimensions of a symbol in the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        symbol: The symbol name to get the dimensions of in the remote R sessions
    Returns:
        A dictionary mapping server names to the dimensions of the specified symbol in the remote R sessions
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    return BaseClient(dscontext).get_dimensions(symbol)


@mcp.tool()
def get_frequencies(ctx: Context[ServerSession, AppContext], session_id: str, symbol: str) -> dict[str, Any]:
    """Get the frequencies of a factor symbol in the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        symbol: The symbol name to get the frequencies of in the remote R sessions
    Returns:
        A dictionary mapping server names to the frequencies of the specified factor symbol in the remote R sessions
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    return BaseClient(dscontext).get_frequencies(symbol)


@mcp.tool()
def get_quantile_means(ctx: Context[ServerSession, AppContext], session_id: str, symbol: str) -> dict[str, Any]:
    """Get the quantiles and means of a numeric symbol in the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        symbol: The symbol name to get the quantiles and means of in the remote R sessions
    Returns:
        A dictionary mapping server names to the quantiles and means of the specified numeric symbol in the remote R sessions
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    return BaseClient(dscontext).get_quantile_means(symbol)


@mcp.tool()
def get_summary(ctx: Context[ServerSession, AppContext], session_id: str, symbol: str) -> dict[str, Any]:
    """Get the summary of a symbol in the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        symbol: The symbol name to get the summary of in the remote R sessions
    Returns:
        A dictionary mapping server names to the summary of the specified symbol in the remote R sessions
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    return BaseClient(dscontext).get_summary(symbol)


@mcp.tool()
def get_mean(ctx: Context[ServerSession, AppContext], session_id: str, symbol: str) -> dict[str, Any]:
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
    return BaseClient(dscontext).get_mean(symbol)


@mcp.tool()
def get_histogram(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    symbol: str,
    num_breaks: int = 20,
    k: int = 3,
    noise: float = 0.25,
) -> list[TextContent | ImageContent]:
    """Get the histogram of a symbol in the connected DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        symbol: The symbol name to get the histogram of in the remote R sessions
        num_breaks: The number of breaks to use for the histogram (default is 20)
        k: The number of the nearest neighbours for which their centroid is calculated (default is 3)
        noise: The noise parameter for the histogram (default is 0.25)
    Returns:
        A list of TextContent and ImageContent objects containing the histogram information and image for the specified symbol in the remote R sessions
    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    return BaseClient(dscontext).get_histogram(symbol, num_breaks=num_breaks, k=k, noise=noise)


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
