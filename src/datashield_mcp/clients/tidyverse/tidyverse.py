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
    
    def filter(
        self,
        df_name: str,
        tidy_expr: str,
        newobj: str
    ) -> None:
        """Keep rows that match a condition.
        
        DataSHIELD Python implementation of dplyr::filter.
        
        Args:
            df_name: Name of server-side data frame or tibble
            tidy_expr: Logical predicate expression (e.g., "mpg > 20 & cyl == 4")
            newobj: Name for new server-side data frame
            
        Example:
            >>> client.filter(
            ...     df_name="mtcars",
            ...     tidy_expr="mpg > 20 & cyl == 4",
            ...     newobj="filtered"
            ... )
        """
        call_expr = make_serverside_call(
            "filterDS",
            tidy_expr,
            [df_name]
        )
        
        logger.info(f"[{self.dscontext.id}] Executing filter: {call_expr}")
        self.dscontext.session.assign(newobj, call_expr)
    
    def mutate(
        self,
        df_name: str,
        tidy_expr: str,
        newobj: str
    ) -> None:
        """Create or modify columns.
        
        DataSHIELD Python implementation of dplyr::mutate.
        
        Args:
            df_name: Name of server-side data frame or tibble
            tidy_expr: Expression(s) for creating/modifying columns
                      (e.g., "new_col = old_col * 2" or "a = b + 1, c = d - 1")
            newobj: Name for new server-side data frame
            
        Example:
            >>> client.mutate(
            ...     df_name="mtcars",
            ...     tidy_expr="mpg_squared = mpg ^ 2, hp_kw = hp * 0.746",
            ...     newobj="transformed"
            ... )
        """
        call_expr = make_serverside_call(
            "mutateDS",
            tidy_expr,
            [df_name]
        )
        
        logger.info(f"[{self.dscontext.id}] Executing mutate: {call_expr}")
        self.dscontext.session.assign(newobj, call_expr)
    
    def arrange(
        self,
        df_name: str,
        tidy_expr: str,
        newobj: str
    ) -> None:
        """Arrange rows by column values.
        
        DataSHIELD Python implementation of dplyr::arrange.
        
        Args:
            df_name: Name of server-side data frame or tibble
            tidy_expr: Expression specifying columns to sort by
                      (e.g., "mpg" or "desc(mpg), cyl")
            newobj: Name for new server-side data frame
            
        Example:
            >>> client.arrange(
            ...     df_name="mtcars",
            ...     tidy_expr="desc(mpg), cyl",
            ...     newobj="sorted"
            ... )
        """
        call_expr = make_serverside_call(
            "arrangeDS",
            tidy_expr,
            [df_name]
        )
        
        logger.info(f"[{self.dscontext.id}] Executing arrange: {call_expr}")
        self.dscontext.session.assign(newobj, call_expr)
    
    def rename(
        self,
        df_name: str,
        tidy_expr: str,
        newobj: str
    ) -> None:
        """Rename columns.
        
        DataSHIELD Python implementation of dplyr::rename.
        
        Args:
            df_name: Name of server-side data frame or tibble
            tidy_expr: Renaming expression(s)
                      (e.g., "new_name = old_name" or "a = b, c = d")
            newobj: Name for new server-side data frame
            
        Example:
            >>> client.rename(
            ...     df_name="mtcars",
            ...     tidy_expr="miles_per_gallon = mpg, cylinders = cyl",
            ...     newobj="renamed"
            ... )
        """
        call_expr = make_serverside_call(
            "renameDS",
            tidy_expr,
            [df_name]
        )
        
        logger.info(f"[{self.dscontext.id}] Executing rename: {call_expr}")
        self.dscontext.session.assign(newobj, call_expr)
    
    def slice(
        self,
        df_name: str,
        tidy_expr: str,
        newobj: str
    ) -> None:
        """Select rows by position.
        
        DataSHIELD Python implementation of dplyr::slice.
        
        Args:
            df_name: Name of server-side data frame or tibble
            tidy_expr: Row positions or ranges
                      (e.g., "1, 5, 10" or "1:10")
            newobj: Name for new server-side data frame
            
        Example:
            >>> client.slice(
            ...     df_name="mtcars",
            ...     tidy_expr="1:10",
            ...     newobj="first_ten"
            ... )
        """
        call_expr = make_serverside_call(
            "sliceDS",
            tidy_expr,
            [df_name]
        )
        
        logger.info(f"[{self.dscontext.id}] Executing slice: {call_expr}")
        self.dscontext.session.assign(newobj, call_expr)
