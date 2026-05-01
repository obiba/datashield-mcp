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
    
    def group_by(
        self,
        df_name: str,
        tidy_expr: str,
        newobj: str
    ) -> None:
        """Group data by one or more variables.
        
        DataSHIELD Python implementation of dplyr::group_by.
        
        Args:
            df_name: Name of server-side data frame or tibble
            tidy_expr: Variables to group by (e.g., "cyl" or "cyl, gear")
            newobj: Name for new server-side grouped data frame
            
        Example:
            >>> client.group_by(
            ...     df_name="mtcars",
            ...     tidy_expr="cyl, gear",
            ...     newobj="grouped"
            ... )
        """
        call_expr = make_serverside_call(
            "groupByDS",
            tidy_expr,
            [df_name]
        )
        
        logger.info(f"[{self.dscontext.id}] Executing group_by: {call_expr}")
        self.dscontext.session.assign(newobj, call_expr)
    
    def ungroup(
        self,
        df_name: str,
        newobj: str
    ) -> None:
        """Remove grouping from a grouped data frame.
        
        DataSHIELD Python implementation of dplyr::ungroup.
        
        Args:
            df_name: Name of server-side grouped data frame
            newobj: Name for new server-side ungrouped data frame
            
        Example:
            >>> client.ungroup(
            ...     df_name="grouped_mtcars",
            ...     newobj="ungrouped"
            ... )
        """
        call_expr = make_serverside_call(
            "ungroupDS",
            None,
            [df_name]
        )
        
        logger.info(f"[{self.dscontext.id}] Executing ungroup: {call_expr}")
        self.dscontext.session.assign(newobj, call_expr)
    
    def group_keys(
        self,
        df_name: str,
        newobj: str
    ) -> None:
        """Get the grouping keys from a grouped data frame.
        
        DataSHIELD Python implementation of dplyr::group_keys.
        
        Args:
            df_name: Name of server-side grouped data frame
            newobj: Name for new server-side data frame containing group keys
            
        Example:
            >>> client.group_keys(
            ...     df_name="grouped_mtcars",
            ...     newobj="keys"
            ... )
        """
        call_expr = make_serverside_call(
            "groupKeysDS",
            None,
            [df_name]
        )
        
        logger.info(f"[{self.dscontext.id}] Executing group_keys: {call_expr}")
        self.dscontext.session.assign(newobj, call_expr)
    
    def distinct(
        self,
        df_name: str,
        tidy_expr: str | None,
        newobj: str
    ) -> None:
        """Select distinct/unique rows.
        
        DataSHIELD Python implementation of dplyr::distinct.
        
        Args:
            df_name: Name of server-side data frame or tibble
            tidy_expr: Optional column specification. If None, uses all columns.
                      (e.g., None for all columns, or "cyl, gear" for specific columns)
            newobj: Name for new server-side data frame
            
        Example:
            >>> # All columns
            >>> client.distinct(
            ...     df_name="mtcars",
            ...     tidy_expr=None,
            ...     newobj="unique"
            ... )
            >>> # Specific columns
            >>> client.distinct(
            ...     df_name="mtcars",
            ...     tidy_expr="cyl, gear",
            ...     newobj="unique"
            ... )
        """
        call_expr = make_serverside_call(
            "distinctDS",
            tidy_expr,
            [df_name]
        )
        
        logger.info(f"[{self.dscontext.id}] Executing distinct: {call_expr}")
        self.dscontext.session.assign(newobj, call_expr)
    
    def bind_rows(
        self,
        df_names: list[str],
        newobj: str
    ) -> None:
        """Bind multiple data frames by row.
        
        DataSHIELD Python implementation of dplyr::bind_rows.
        
        Args:
            df_names: List of server-side data frame names to bind
            newobj: Name for new server-side data frame
            
        Example:
            >>> client.bind_rows(
            ...     df_names=["df1", "df2", "df3"],
            ...     newobj="combined"
            ... )
        """
        call_expr = make_serverside_call(
            "bindRowsDS",
            None,
            df_names
        )
        
        logger.info(f"[{self.dscontext.id}] Executing bind_rows: {call_expr}")
        self.dscontext.session.assign(newobj, call_expr)
    
    def bind_cols(
        self,
        df_names: list[str],
        newobj: str
    ) -> None:
        """Bind multiple data frames by column.
        
        DataSHIELD Python implementation of dplyr::bind_cols.
        
        Args:
            df_names: List of server-side data frame names to bind
            newobj: Name for new server-side data frame
            
        Example:
            >>> client.bind_cols(
            ...     df_names=["df1", "df2"],
            ...     newobj="combined"
            ... )
        """
        call_expr = make_serverside_call(
            "bindColsDS",
            None,
            df_names
        )
        
        logger.info(f"[{self.dscontext.id}] Executing bind_cols: {call_expr}")
        self.dscontext.session.assign(newobj, call_expr)
    
    def if_else(
        self,
        condition: str,
        true_value: str,
        false_value: str,
        missing_value: str | None = None,
        newobj: str = ""
    ) -> None:
        """Vectorized if-else statement.
        
        DataSHIELD Python implementation of dplyr::if_else.
        
        Args:
            condition: Logical condition expression
            true_value: Value when condition is TRUE
            false_value: Value when condition is FALSE
            missing_value: Optional value for NA/missing (defaults to None)
            newobj: Name for new server-side object
            
        Example:
            >>> client.if_else(
            ...     condition="mpg > 20",
            ...     true_value="'high'",
            ...     false_value="'low'",
            ...     newobj="mpg_category"
            ... )
        """
        # Build argument list based on whether missing_value is provided
        args = [condition, true_value, false_value]
        if missing_value is not None:
            args.append(missing_value)
        
        # Encode each argument as a tidy expression
        # Join them with commas to create a single expression string
        tidy_expr = ", ".join(args)
        
        call_expr = make_serverside_call(
            "ifElseDS",
            tidy_expr,
            []
        )
        
        logger.info(f"[{self.dscontext.id}] Executing if_else: {call_expr}")
        self.dscontext.session.assign(newobj, call_expr)
    
    def case_when(
        self,
        cases: str,
        newobj: str
    ) -> None:
        """Vectorized multi-way if-else (case statement).
        
        DataSHIELD Python implementation of dplyr::case_when.
        
        Args:
            cases: Case expressions in the form "condition ~ value, condition ~ value, ..."
                  (e.g., "mpg > 25 ~ 'excellent', mpg > 20 ~ 'good', TRUE ~ 'average'")
            newobj: Name for new server-side object
            
        Example:
            >>> client.case_when(
            ...     cases="mpg > 25 ~ 'excellent', mpg > 20 ~ 'good', TRUE ~ 'average'",
            ...     newobj="mpg_rating"
            ... )
        """
        call_expr = make_serverside_call(
            "caseWhenDS",
            cases,
            []
        )
        
        logger.info(f"[{self.dscontext.id}] Executing case_when: {call_expr}")
        self.dscontext.session.assign(newobj, call_expr)
