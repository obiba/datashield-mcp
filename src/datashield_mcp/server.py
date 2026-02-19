from collections.abc import AsyncIterator
import sys
import uuid
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession
from datashield import DSConfig, DSSession, DSLoginBuilder

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
        logging.StreamHandler(sys.stderr)
    ]
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
    logins = DSLoginBuilder(names = server_names).build()
    session = DSSession(logins)
    session.open()
    logger.info(f"Opened DataSHIELD session with servers: {session.get_connection_names()} / {server_names}")
    # store the session for later use
    session_id = str(uuid.uuid4())
    ctx.request_context.lifespan_context.sessions[session_id] = session
    return {"session_id": session_id, "servers": session.get_connection_names()}

@mcp.tool()
def close(ctx: Context[ServerSession, AppContext], session_id: str) -> None:
    """Close a DataSHIELD session"""
    session = ctx.request_context.lifespan_context.sessions.get(session_id)
    if session:
        session.close()
        del ctx.request_context.lifespan_context.sessions[session_id]

@mcp.tool()
def list_tables(ctx: Context[ServerSession, AppContext], session_id: str) -> dict[str, list[str]]:
    """List tables available in the connected DataSHIELD session"""
    session = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not session:
        raise ValueError("Not connected to DataSHIELD")
    tables = session.tables()
    logger.info(f"Available tables in session {session_id}: {tables}")
    return tables

@mcp.tool()
def assign_tables(ctx: Context[ServerSession, AppContext], session_id: str, symbol: str, tables: dict[str, str]) -> dict[str, list[str]]:
    """Assign tables to the connected DataSHIELD session"""
    session = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not session:
        raise ValueError("Not connected to DataSHIELD")
    session.assign_table(symbol, tables=tables)
    symbols = session.ls()
    logger.info(f"Assigned tables to symbol '{symbol}' in session {session_id}. Current symbols: {symbols}")
    return symbols

@mcp.tool()
def list_colnames(ctx: Context[ServerSession, AppContext], session_id: str, symbol: str) -> dict[str, list[str]]:
    """List column names of a table in the connected DataSHIELD session"""
    session = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not session:
        raise ValueError("Not connected to DataSHIELD")
    colnames = session.aggregate(f"colnamesDS('{symbol}')")
    logger.info(f"Column names for symbol '{symbol}' in session {session_id}: {colnames}")
    return colnames

@mcp.tool()
def get_class(ctx: Context[ServerSession, AppContext], session_id: str, symbol: str) -> dict[str, str]:
    """Get the class of a symbol in the connected DataSHIELD session"""
    session = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not session:
        raise ValueError("Not connected to DataSHIELD")
    colnames = session.aggregate(f"classDS('{symbol}')")
    logger.info(f"Class for symbol '{symbol}' in session {session_id}: {colnames}")
    return colnames

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