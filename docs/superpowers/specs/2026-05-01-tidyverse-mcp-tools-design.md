# Design: Tidyverse MCP Tools

**Date:** 2026-05-01  
**Status:** Approved

## Overview

Extend the DataSHIELD MCP server with 15 new tools that expose tidyverse client functionality to AI agents. This enables natural language data manipulation commands like "filter patients with BMI > 25" or "create age group columns" without requiring users to write R code.

## Goals

- Enable AI agents to perform dplyr-style data manipulation operations on DataSHIELD sessions
- Maintain consistency with existing MCP server patterns
- Provide clear, discoverable tools for each tidyverse operation
- Support the full range of tidyverse operations implemented in the Python client

## Architecture

### Tool Organization

Add 15 new MCP tools to `src/datashield_mcp/server.py`:

**TidyverseClient tools (14 tools):**
- Data selection: `tidyverse_select()`, `tidyverse_filter()`
- Data transformation: `tidyverse_mutate()`, `tidyverse_arrange()`, `tidyverse_rename()`, `tidyverse_slice()`
- Grouping: `tidyverse_group_by()`, `tidyverse_ungroup()`, `tidyverse_group_keys()`
- Combining: `tidyverse_distinct()`, `tidyverse_bind_rows()`, `tidyverse_bind_cols()`
- Conditionals: `tidyverse_if_else()`, `tidyverse_case_when()`

**TibbleClient tools (1 tool):**
- `tibble_as_tibble()` - convert data frame to tibble

### Import Updates

Add to line 14 in `server.py`:
```python
from datashield_mcp.clients.tidyverse import TidyverseClient, TibbleClient
```

### Tool Implementation Pattern

Each tool follows the existing pattern in `server.py`:

```python
@mcp.tool()
def tidyverse_<operation>(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    df_name: str,
    tidy_expr: str,  # or other params depending on operation
    newobj: str
) -> dict[str, list[str]]:
    """Tool description with Args, Returns, Raises sections."""
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    
    TidyverseClient(dscontext).<operation>(
        df_name=df_name,
        tidy_expr=tidy_expr,
        newobj=newobj
    )
    
    return dscontext.session.ls()  # Return updated symbol list
```

## Tool Specifications

### Common Parameters

All tools include:
- `ctx: Context[ServerSession, AppContext]` - MCP context
- `session_id: str` - DataSHIELD session ID

### Standard Parameters

Most tools use:
- `df_name: str` - Name of server-side dataframe
- `tidy_expr: str` - R-style expression
- `newobj: str` - Name for the result

### Special Cases

**No tidy_expr parameter:**
- `tidyverse_ungroup(ctx, session_id, df_name, newobj)`
- `tidyverse_group_keys(ctx, session_id, df_name, newobj)`
- `tibble_as_tibble(ctx, session_id, df_name, newobj)`

**List of dataframes instead of single df_name:**
- `tidyverse_bind_rows(ctx, session_id, df_names: list[str], newobj)`
- `tidyverse_bind_cols(ctx, session_id, df_names: list[str], newobj)`

**Optional tidy_expr:**
- `tidyverse_distinct(ctx, session_id, df_name, tidy_expr: str | None, newobj)`

**Different parameters:**
- `tidyverse_if_else(ctx, session_id, condition: str, true_value: str, false_value: str, missing_value: str | None, newobj: str)`
- `tidyverse_case_when(ctx, session_id, cases: str, newobj: str)`

### Return Values

All tools return `dict[str, list[str]]` - the updated symbol list from `dscontext.session.ls()`, showing what objects exist in the DataSHIELD session after the operation.

### Error Handling

All tools validate session connectivity:
```python
dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
if not dscontext or not dscontext.session:
    raise ValueError("Not connected to DataSHIELD")
```

## Documentation

### Docstring Format

Each tool includes comprehensive docstrings:

```python
"""<One-line summary>

Args:
    ctx: The MCP tool context, which provides access to the application context and session information
    session_id: The session ID of the connected DataSHIELD session
    df_name: Name of server-side data frame or tibble
    tidy_expr: <Expression format description>
    newobj: Name for new server-side data frame

Returns:
    A dictionary mapping server names to lists of available symbols after the operation

Raises:
    ValueError: If the session ID is invalid or not connected to DataSHIELD
"""
```

### Example Docstrings

**tidyverse_select:**
```python
"""Select columns from a DataSHIELD data frame

Args:
    ctx: The MCP tool context, which provides access to the application context and session information
    session_id: The session ID of the connected DataSHIELD session
    df_name: Name of server-side data frame to select columns from
    tidy_expr: Column selection expression (e.g., "mpg, cyl" or "starts_with('m')")
    newobj: Name for the new data frame with selected columns

Returns:
    A dictionary mapping server names to lists of available symbols after selection

Raises:
    ValueError: If the session ID is invalid or not connected to DataSHIELD
"""
```

**tidyverse_filter:**
```python
"""Filter rows in a DataSHIELD data frame based on logical conditions

Args:
    ctx: The MCP tool context, which provides access to the application context and session information
    session_id: The session ID of the connected DataSHIELD session
    df_name: Name of server-side data frame to filter
    tidy_expr: Logical predicate expression (e.g., "mpg > 20", "cyl == 4 & mpg > 20")
    newobj: Name for the filtered data frame

Returns:
    A dictionary mapping server names to lists of available symbols after filtering

Raises:
    ValueError: If the session ID is invalid or not connected to DataSHIELD
"""
```

**tidyverse_bind_rows:**
```python
"""Bind multiple DataSHIELD data frames by rows

Args:
    ctx: The MCP tool context, which provides access to the application context and session information
    session_id: The session ID of the connected DataSHIELD session
    df_names: List of server-side data frame names to bind together
    newobj: Name for the combined data frame

Returns:
    A dictionary mapping server names to lists of available symbols after binding

Raises:
    ValueError: If the session ID is invalid or not connected to DataSHIELD
"""
```

**tidyverse_if_else:**
```python
"""Create a conditional vector using if-else logic in a DataSHIELD session

Args:
    ctx: The MCP tool context, which provides access to the application context and session information
    session_id: The session ID of the connected DataSHIELD session
    condition: Logical condition expression (e.g., "df$mpg > 20")
    true_value: Value when condition is TRUE (e.g., "'high'" or "1")
    false_value: Value when condition is FALSE (e.g., "'low'" or "0")
    missing_value: Optional value for NA/missing cases (e.g., "'unknown'" or "NA")
    newobj: Name for the new conditional vector

Returns:
    A dictionary mapping server names to lists of available symbols after operation

Raises:
    ValueError: If the session ID is invalid or not connected to DataSHIELD
"""
```

## Testing Strategy

### Basic Unit Tests

Create `tests/test_server_tidyverse.py` with basic tests that:
- Mock MCP Context and DSContext
- Verify each tool calls the correct client method with correct parameters
- Verify error handling for invalid session IDs
- Test parameter variations for special cases (optional parameters, lists, etc.)

### Test Pattern

```python
from unittest.mock import MagicMock, Mock
import pytest

def test_tidyverse_select_tool():
    """Test that tidyverse_select calls TidyverseClient.select correctly."""
    # Setup mocks
    mock_session = MagicMock()
    mock_session.ls.return_value = {"server1": ["mtcars", "subset"]}
    
    mock_dscontext = MagicMock()
    mock_dscontext.session = mock_session
    
    mock_ctx = MagicMock()
    mock_ctx.request_context.lifespan_context.sessions = {
        "test-session": mock_dscontext
    }
    
    # Call tool
    from datashield_mcp.server import tidyverse_select
    result = tidyverse_select(
        ctx=mock_ctx,
        session_id="test-session",
        df_name="mtcars",
        tidy_expr="mpg, cyl",
        newobj="subset"
    )
    
    # Verify result
    assert result == {"server1": ["mtcars", "subset"]}
    mock_session.ls.assert_called_once()

def test_tidyverse_tool_invalid_session():
    """Test error handling for invalid session ID."""
    mock_ctx = MagicMock()
    mock_ctx.request_context.lifespan_context.sessions = {}
    
    from datashield_mcp.server import tidyverse_select
    with pytest.raises(ValueError, match="Not connected to DataSHIELD"):
        tidyverse_select(
            ctx=mock_ctx,
            session_id="invalid-session",
            df_name="mtcars",
            tidy_expr="mpg",
            newobj="subset"
        )
```

### Test Coverage

Basic tests will cover:
- Standard tools (select, filter, mutate, arrange, rename, slice)
- Grouping tools (group_by, ungroup, group_keys)
- Combining tools (distinct, bind_rows, bind_cols)
- Conditional tools (if_else, case_when)
- Tibble tool (as_tibble)
- Error cases (invalid session)
- Special parameter cases (optional tidy_expr, list parameters)

Approximately 20-25 test cases total.

## Implementation Details

### File Changes

**src/datashield_mcp/server.py:**
- Add import: `from datashield_mcp.clients.tidyverse import TidyverseClient, TibbleClient`
- Add 15 new `@mcp.tool()` decorated functions
- Estimated addition: ~240 lines (15 tools × ~16 lines average per tool)
- Final size: ~900 lines (currently 662 lines)

**tests/test_server_tidyverse.py:**
- New file with 20-25 basic unit tests
- Estimated size: ~400-500 lines

### Tool Placement in server.py

Add tidyverse tools after the existing model tools (after line 638, after `get_glm()`), organized as:

```python
# Tidyverse Operations

# Data Selection
@mcp.tool()
def tidyverse_select(...): ...

@mcp.tool()
def tidyverse_filter(...): ...

# Data Transformation
@mcp.tool()
def tidyverse_mutate(...): ...

@mcp.tool()
def tidyverse_arrange(...): ...

@mcp.tool()
def tidyverse_rename(...): ...

@mcp.tool()
def tidyverse_slice(...): ...

# Grouping Operations
@mcp.tool()
def tidyverse_group_by(...): ...

@mcp.tool()
def tidyverse_ungroup(...): ...

@mcp.tool()
def tidyverse_group_keys(...): ...

# Combining Operations
@mcp.tool()
def tidyverse_distinct(...): ...

@mcp.tool()
def tidyverse_bind_rows(...): ...

@mcp.tool()
def tidyverse_bind_cols(...): ...

# Conditional Operations
@mcp.tool()
def tidyverse_if_else(...): ...

@mcp.tool()
def tidyverse_case_when(...): ...

# Tibble Operations
@mcp.tool()
def tibble_as_tibble(...): ...
```

## Usage Examples

### Example 1: Filter and Select
AI agent receives: "Show me diabetes patients with high BMI, keep only age and gender columns"

Generated MCP tool calls:
```python
# Filter for high BMI
tidyverse_filter(
    session_id="abc123",
    df_name="diabetes_data",
    tidy_expr="bmi > 30",
    newobj="high_bmi"
)

# Select columns
tidyverse_select(
    session_id="abc123",
    df_name="high_bmi",
    tidy_expr="age, gender",
    newobj="final_data"
)
```

### Example 2: Create Age Groups
AI agent receives: "Create age groups: young (<40), middle (40-60), senior (>60)"

Generated MCP tool call:
```python
tidyverse_case_when(
    session_id="abc123",
    cases="age < 40 ~ 'young', age >= 40 & age <= 60 ~ 'middle', age > 60 ~ 'senior'",
    newobj="age_groups"
)
```

### Example 3: Combine and Summarize by Groups
AI agent receives: "Combine all cohort data and calculate means by gender"

Generated MCP tool calls:
```python
# Combine dataframes
tidyverse_bind_rows(
    session_id="abc123",
    df_names=["cohort1", "cohort2", "cohort3"],
    newobj="combined"
)

# Group by gender
tidyverse_group_by(
    session_id="abc123",
    df_name="combined",
    tidy_expr="gender",
    newobj="grouped"
)

# (Then use existing aggregate functions like get_mean)
```

## Benefits

1. **Natural Language Interface:** Users can describe data operations in plain language
2. **Consistency:** Tools follow existing MCP server patterns
3. **Discoverability:** Each operation is a separate tool, easy for AI agents to find
4. **Complete Coverage:** All 15 tidyverse client methods are exposed
5. **Error Handling:** Clear validation and error messages
6. **Documentation:** Comprehensive docstrings help AI agents understand usage

## Constraints

1. **Server File Size:** `server.py` will grow to ~900 lines (still manageable)
2. **Tool Namespace:** 15 new tools in MCP tool list (clear naming prevents confusion)
3. **Expression Syntax:** Users still need to understand R expression syntax (mitigated by AI agent assistance)
4. **Testing:** Basic unit tests only (no integration tests with live DataSHIELD servers)

## Success Criteria

1. All 15 tidyverse tools implemented and functional
2. Tools follow existing MCP server patterns
3. Comprehensive docstrings for AI agent usage
4. Basic unit tests pass (20-25 tests)
5. AI agents can successfully chain tidyverse operations
6. No regressions in existing MCP server functionality
