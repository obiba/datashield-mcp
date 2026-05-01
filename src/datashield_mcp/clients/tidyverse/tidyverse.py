"""TidyverseClient for dplyr operations."""
from datashield_mcp.models import DSContext
from datashield_mcp.logs import logger
from datashield_mcp.clients.tidyverse.utils import make_serverside_call


class TidyverseClient:
    """Client for tidyverse dplyr operations on DataSHIELD sessions.
    
    This client provides Python methods that correspond to dplyr functions
    in the dsTidyverseClient R package. Each method constructs and executes
    DataSHIELD server-side calls.
    """
    
    def __init__(self, dscontext: DSContext):
        """Initialize the TidyverseClient.
        
        Args:
            dscontext: The DataSHIELD session context to use for operations
        """
        self.dscontext = dscontext
    
    def select(
        self, 
        df_name: str, 
        tidy_expr: str,
        newobj: str
    ) -> None:
        """Keep or drop columns using their names and types.
        
        DataSHIELD Python implementation of dplyr::select.
        
        Args:
            df_name: Name of server-side data frame or tibble
            tidy_expr: Tidy select expression (e.g., "mpg, cyl" or "starts_with('m')")
            newobj: Name for new server-side data frame
            
        Example:
            >>> client.select(
            ...     df_name="mtcars",
            ...     tidy_expr="mpg, starts_with('c')",
            ...     newobj="subset"
            ... )
        """
        call_expr = make_serverside_call(
            "selectDS", 
            tidy_expr, 
            [df_name]
        )
        
        logger.info(f"[{self.dscontext.id}] Executing select: {call_expr}")
        self.dscontext.session.assign(newobj, call_expr)
