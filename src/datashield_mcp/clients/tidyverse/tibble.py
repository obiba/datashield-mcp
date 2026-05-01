"""TibbleClient for tibble operations."""

from datashield_mcp.models import DSContext
from datashield_mcp.logs import logger
from datashield_mcp.clients.tidyverse.utils import make_serverside_call


class TibbleClient:
    """Client for tibble operations on DataSHIELD sessions.

    This client provides Python methods that correspond to tibble functions
    in the dsTidyverseClient R package.
    """

    def __init__(self, dscontext: DSContext):
        """Initialize the TibbleClient.

        Args:
            dscontext: The DataSHIELD session context to use for operations
        """
        self.dscontext = dscontext

    def as_tibble(self, df_name: str, newobj: str) -> None:
        """Convert a data frame to a tibble.

        DataSHIELD Python implementation of tibble::as_tibble.

        Args:
            df_name: Name of server-side data frame
            newobj: Name for new server-side tibble

        Example:
            >>> client.as_tibble(
            ...     df_name="mtcars",
            ...     newobj="mtcars_tibble"
            ... )
        """
        call_expr = make_serverside_call("asTibbleDS", None, [df_name])

        logger.info(f"[{self.dscontext.id}] Executing as_tibble: {call_expr}")
        self.dscontext.session.assign(newobj, call_expr)
