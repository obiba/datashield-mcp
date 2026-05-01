# Tidyverse MCP Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose all 15 tidyverse client methods as MCP tools in the DataSHIELD server to enable AI agents to perform dplyr-style data manipulation via natural language.

**Architecture:** Add 15 individual `@mcp.tool()` decorated functions to `server.py` following existing patterns. Each tool extracts DSContext from the session, instantiates TidyverseClient or TibbleClient, calls the corresponding method, and returns the updated symbol list.

**Tech Stack:** Python 3.11+, FastMCP, DataSHIELD Python client, pytest

---

## File Structure

**Files to modify:**
- `src/datashield_mcp/server.py` - Add 15 new MCP tools and import statement

**Files to create:**
- `tests/test_server_tidyverse.py` - Basic unit tests for the new tools

---

## Task 1: Add Import and Data Selection Tools (select, filter)

**Files:**
- Modify: `src/datashield_mcp/server.py:14-15`
- Modify: `src/datashield_mcp/server.py:638` (after get_glm)
- Create: `tests/test_server_tidyverse.py`

- [ ] **Step 1: Add tidyverse imports to server.py**

Add after line 14 in `src/datashield_mcp/server.py`:
```python
from datashield_mcp.clients.tidyverse import TidyverseClient, TibbleClient
```

- [ ] **Step 2: Add tidyverse_select tool**

Add after line 638 (after get_glm function) in `src/datashield_mcp/server.py`:
```python


# Tidyverse Operations

# Data Selection
@mcp.tool()
def tidyverse_select(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    df_name: str,
    tidy_expr: str,
    newobj: str,
) -> dict[str, list[str]]:
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
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    
    TidyverseClient(dscontext).select(
        df_name=df_name,
        tidy_expr=tidy_expr,
        newobj=newobj
    )
    
    return dscontext.session.ls()


@mcp.tool()
def tidyverse_filter(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    df_name: str,
    tidy_expr: str,
    newobj: str,
) -> dict[str, list[str]]:
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
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    
    TidyverseClient(dscontext).filter(
        df_name=df_name,
        tidy_expr=tidy_expr,
        newobj=newobj
    )
    
    return dscontext.session.ls()
```

- [ ] **Step 3: Create test file with basic tests**

Create `tests/test_server_tidyverse.py`:
```python
"""Tests for tidyverse MCP tools."""
from unittest.mock import MagicMock
import pytest

from datashield_mcp.server import tidyverse_select, tidyverse_filter


def create_mock_context(session_id: str = "test-session"):
    """Helper to create a mock MCP context with DSContext."""
    mock_session = MagicMock()
    mock_session.ls.return_value = {"server1": ["mtcars", "subset"]}
    
    mock_dscontext = MagicMock()
    mock_dscontext.session = mock_session
    
    mock_ctx = MagicMock()
    mock_ctx.request_context.lifespan_context.sessions = {
        session_id: mock_dscontext
    }
    
    return mock_ctx, mock_dscontext


def test_tidyverse_select():
    """Test tidyverse_select tool calls TidyverseClient.select."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tidyverse_select(
        ctx=mock_ctx,
        session_id="test-session",
        df_name="mtcars",
        tidy_expr="mpg, cyl",
        newobj="subset"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_filter():
    """Test tidyverse_filter tool calls TidyverseClient.filter."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tidyverse_filter(
        ctx=mock_ctx,
        session_id="test-session",
        df_name="mtcars",
        tidy_expr="mpg > 20",
        newobj="filtered"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_tool_invalid_session():
    """Test error handling for invalid session ID."""
    mock_ctx = MagicMock()
    mock_ctx.request_context.lifespan_context.sessions = {}
    
    with pytest.raises(ValueError, match="Not connected to DataSHIELD"):
        tidyverse_select(
            ctx=mock_ctx,
            session_id="invalid-session",
            df_name="mtcars",
            tidy_expr="mpg",
            newobj="subset"
        )
```

- [ ] **Step 4: Run tests to verify implementation**

```bash
cd /home/yannick/projects/datashield-mcp
pytest tests/test_server_tidyverse.py -v
```

Expected: 3 tests pass

- [ ] **Step 5: Commit**

```bash
cd /home/yannick/projects/datashield-mcp
git add src/datashield_mcp/server.py tests/test_server_tidyverse.py
git commit -m "feat(mcp): add tidyverse_select and tidyverse_filter tools"
```

---

## Task 2: Add Data Transformation Tools (mutate, arrange, rename, slice)

**Files:**
- Modify: `src/datashield_mcp/server.py` (after tidyverse_filter)
- Modify: `tests/test_server_tidyverse.py`

- [ ] **Step 1: Add tidyverse_mutate tool**

Add after tidyverse_filter in `src/datashield_mcp/server.py`:
```python


# Data Transformation
@mcp.tool()
def tidyverse_mutate(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    df_name: str,
    tidy_expr: str,
    newobj: str,
) -> dict[str, list[str]]:
    """Create or modify columns in a DataSHIELD data frame

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        df_name: Name of server-side data frame to mutate
        tidy_expr: Mutation expression(s) (e.g., "mpg_squared = mpg ^ 2" or "a = b + 1, c = d - 1")
        newobj: Name for the mutated data frame

    Returns:
        A dictionary mapping server names to lists of available symbols after mutation

    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    
    TidyverseClient(dscontext).mutate(
        df_name=df_name,
        tidy_expr=tidy_expr,
        newobj=newobj
    )
    
    return dscontext.session.ls()


@mcp.tool()
def tidyverse_arrange(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    df_name: str,
    tidy_expr: str,
    newobj: str,
) -> dict[str, list[str]]:
    """Arrange rows in a DataSHIELD data frame by column values

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        df_name: Name of server-side data frame to arrange
        tidy_expr: Sorting expression (e.g., "mpg" or "desc(mpg), cyl")
        newobj: Name for the arranged data frame

    Returns:
        A dictionary mapping server names to lists of available symbols after arranging

    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    
    TidyverseClient(dscontext).arrange(
        df_name=df_name,
        tidy_expr=tidy_expr,
        newobj=newobj
    )
    
    return dscontext.session.ls()


@mcp.tool()
def tidyverse_rename(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    df_name: str,
    tidy_expr: str,
    newobj: str,
) -> dict[str, list[str]]:
    """Rename columns in a DataSHIELD data frame

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        df_name: Name of server-side data frame with columns to rename
        tidy_expr: Renaming expression(s) (e.g., "new_name = old_name" or "a = b, c = d")
        newobj: Name for the data frame with renamed columns

    Returns:
        A dictionary mapping server names to lists of available symbols after renaming

    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    
    TidyverseClient(dscontext).rename(
        df_name=df_name,
        tidy_expr=tidy_expr,
        newobj=newobj
    )
    
    return dscontext.session.ls()


@mcp.tool()
def tidyverse_slice(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    df_name: str,
    tidy_expr: str,
    newobj: str,
) -> dict[str, list[str]]:
    """Select rows by position in a DataSHIELD data frame

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        df_name: Name of server-side data frame to slice
        tidy_expr: Row positions or ranges (e.g., "1, 5, 10" or "1:10")
        newobj: Name for the sliced data frame

    Returns:
        A dictionary mapping server names to lists of available symbols after slicing

    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    
    TidyverseClient(dscontext).slice(
        df_name=df_name,
        tidy_expr=tidy_expr,
        newobj=newobj
    )
    
    return dscontext.session.ls()
```

- [ ] **Step 2: Add tests for transformation tools**

Add to `tests/test_server_tidyverse.py`:
```python
from datashield_mcp.server import (
    tidyverse_mutate,
    tidyverse_arrange,
    tidyverse_rename,
    tidyverse_slice,
)


def test_tidyverse_mutate():
    """Test tidyverse_mutate tool calls TidyverseClient.mutate."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tidyverse_mutate(
        ctx=mock_ctx,
        session_id="test-session",
        df_name="mtcars",
        tidy_expr="mpg_squared = mpg ^ 2",
        newobj="mutated"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_arrange():
    """Test tidyverse_arrange tool calls TidyverseClient.arrange."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tidyverse_arrange(
        ctx=mock_ctx,
        session_id="test-session",
        df_name="mtcars",
        tidy_expr="desc(mpg)",
        newobj="sorted"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_rename():
    """Test tidyverse_rename tool calls TidyverseClient.rename."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tidyverse_rename(
        ctx=mock_ctx,
        session_id="test-session",
        df_name="mtcars",
        tidy_expr="miles_per_gallon = mpg",
        newobj="renamed"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_slice():
    """Test tidyverse_slice tool calls TidyverseClient.slice."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tidyverse_slice(
        ctx=mock_ctx,
        session_id="test-session",
        df_name="mtcars",
        tidy_expr="1:10",
        newobj="sliced"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()
```

- [ ] **Step 3: Run tests to verify implementation**

```bash
cd /home/yannick/projects/datashield-mcp
pytest tests/test_server_tidyverse.py -v
```

Expected: 7 tests pass (3 from Task 1 + 4 new)

- [ ] **Step 4: Commit**

```bash
cd /home/yannick/projects/datashield-mcp
git add src/datashield_mcp/server.py tests/test_server_tidyverse.py
git commit -m "feat(mcp): add data transformation tools (mutate, arrange, rename, slice)"
```

---

## Task 3: Add Grouping Tools (group_by, ungroup, group_keys)

**Files:**
- Modify: `src/datashield_mcp/server.py` (after tidyverse_slice)
- Modify: `tests/test_server_tidyverse.py`

- [ ] **Step 1: Add grouping tools**

Add after tidyverse_slice in `src/datashield_mcp/server.py`:
```python


# Grouping Operations
@mcp.tool()
def tidyverse_group_by(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    df_name: str,
    tidy_expr: str,
    newobj: str,
) -> dict[str, list[str]]:
    """Group a DataSHIELD data frame by one or more variables

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        df_name: Name of server-side data frame to group
        tidy_expr: Variables to group by (e.g., "cyl" or "cyl, gear")
        newobj: Name for the grouped data frame

    Returns:
        A dictionary mapping server names to lists of available symbols after grouping

    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    
    TidyverseClient(dscontext).group_by(
        df_name=df_name,
        tidy_expr=tidy_expr,
        newobj=newobj
    )
    
    return dscontext.session.ls()


@mcp.tool()
def tidyverse_ungroup(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    df_name: str,
    newobj: str,
) -> dict[str, list[str]]:
    """Remove grouping from a grouped DataSHIELD data frame

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        df_name: Name of server-side grouped data frame
        newobj: Name for the ungrouped data frame

    Returns:
        A dictionary mapping server names to lists of available symbols after ungrouping

    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    
    TidyverseClient(dscontext).ungroup(
        df_name=df_name,
        newobj=newobj
    )
    
    return dscontext.session.ls()


@mcp.tool()
def tidyverse_group_keys(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    df_name: str,
    newobj: str,
) -> dict[str, list[str]]:
    """Get the grouping keys from a grouped DataSHIELD data frame

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        df_name: Name of server-side grouped data frame
        newobj: Name for the data frame containing group keys

    Returns:
        A dictionary mapping server names to lists of available symbols after extracting keys

    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    
    TidyverseClient(dscontext).group_keys(
        df_name=df_name,
        newobj=newobj
    )
    
    return dscontext.session.ls()
```

- [ ] **Step 2: Add tests for grouping tools**

Add to `tests/test_server_tidyverse.py`:
```python
from datashield_mcp.server import (
    tidyverse_group_by,
    tidyverse_ungroup,
    tidyverse_group_keys,
)


def test_tidyverse_group_by():
    """Test tidyverse_group_by tool calls TidyverseClient.group_by."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tidyverse_group_by(
        ctx=mock_ctx,
        session_id="test-session",
        df_name="mtcars",
        tidy_expr="cyl, gear",
        newobj="grouped"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_ungroup():
    """Test tidyverse_ungroup tool calls TidyverseClient.ungroup."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tidyverse_ungroup(
        ctx=mock_ctx,
        session_id="test-session",
        df_name="grouped_mtcars",
        newobj="ungrouped"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_group_keys():
    """Test tidyverse_group_keys tool calls TidyverseClient.group_keys."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tidyverse_group_keys(
        ctx=mock_ctx,
        session_id="test-session",
        df_name="grouped_mtcars",
        newobj="keys"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()
```

- [ ] **Step 3: Run tests to verify implementation**

```bash
cd /home/yannick/projects/datashield-mcp
pytest tests/test_server_tidyverse.py -v
```

Expected: 10 tests pass (7 from previous tasks + 3 new)

- [ ] **Step 4: Commit**

```bash
cd /home/yannick/projects/datashield-mcp
git add src/datashield_mcp/server.py tests/test_server_tidyverse.py
git commit -m "feat(mcp): add grouping tools (group_by, ungroup, group_keys)"
```

---

## Task 4: Add Combining Tools (distinct, bind_rows, bind_cols)

**Files:**
- Modify: `src/datashield_mcp/server.py` (after tidyverse_group_keys)
- Modify: `tests/test_server_tidyverse.py`

- [ ] **Step 1: Add combining tools**

Add after tidyverse_group_keys in `src/datashield_mcp/server.py`:
```python


# Combining Operations
@mcp.tool()
def tidyverse_distinct(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    df_name: str,
    tidy_expr: str | None,
    newobj: str,
) -> dict[str, list[str]]:
    """Select distinct/unique rows from a DataSHIELD data frame

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        df_name: Name of server-side data frame
        tidy_expr: Optional column specification (None for all columns, or "cyl, gear" for specific)
        newobj: Name for the data frame with distinct rows

    Returns:
        A dictionary mapping server names to lists of available symbols after selecting distinct rows

    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    
    TidyverseClient(dscontext).distinct(
        df_name=df_name,
        tidy_expr=tidy_expr,
        newobj=newobj
    )
    
    return dscontext.session.ls()


@mcp.tool()
def tidyverse_bind_rows(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    df_names: list[str],
    newobj: str,
) -> dict[str, list[str]]:
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
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    
    TidyverseClient(dscontext).bind_rows(
        df_names=df_names,
        newobj=newobj
    )
    
    return dscontext.session.ls()


@mcp.tool()
def tidyverse_bind_cols(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    df_names: list[str],
    newobj: str,
) -> dict[str, list[str]]:
    """Bind multiple DataSHIELD data frames by columns

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
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    
    TidyverseClient(dscontext).bind_cols(
        df_names=df_names,
        newobj=newobj
    )
    
    return dscontext.session.ls()
```

- [ ] **Step 2: Add tests for combining tools**

Add to `tests/test_server_tidyverse.py`:
```python
from datashield_mcp.server import (
    tidyverse_distinct,
    tidyverse_bind_rows,
    tidyverse_bind_cols,
)


def test_tidyverse_distinct():
    """Test tidyverse_distinct tool calls TidyverseClient.distinct."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tidyverse_distinct(
        ctx=mock_ctx,
        session_id="test-session",
        df_name="mtcars",
        tidy_expr="cyl, gear",
        newobj="unique"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_distinct_all_columns():
    """Test tidyverse_distinct with None (all columns)."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tidyverse_distinct(
        ctx=mock_ctx,
        session_id="test-session",
        df_name="mtcars",
        tidy_expr=None,
        newobj="unique"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_bind_rows():
    """Test tidyverse_bind_rows tool calls TidyverseClient.bind_rows."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tidyverse_bind_rows(
        ctx=mock_ctx,
        session_id="test-session",
        df_names=["df1", "df2", "df3"],
        newobj="combined"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_bind_cols():
    """Test tidyverse_bind_cols tool calls TidyverseClient.bind_cols."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tidyverse_bind_cols(
        ctx=mock_ctx,
        session_id="test-session",
        df_names=["df1", "df2"],
        newobj="combined"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()
```

- [ ] **Step 3: Run tests to verify implementation**

```bash
cd /home/yannick/projects/datashield-mcp
pytest tests/test_server_tidyverse.py -v
```

Expected: 14 tests pass (10 from previous tasks + 4 new)

- [ ] **Step 4: Commit**

```bash
cd /home/yannick/projects/datashield-mcp
git add src/datashield_mcp/server.py tests/test_server_tidyverse.py
git commit -m "feat(mcp): add combining tools (distinct, bind_rows, bind_cols)"
```

---

## Task 5: Add Conditional Tools (if_else, case_when) and Tibble Tool (as_tibble)

**Files:**
- Modify: `src/datashield_mcp/server.py` (after tidyverse_bind_cols)
- Modify: `tests/test_server_tidyverse.py`

- [ ] **Step 1: Add conditional and tibble tools**

Add after tidyverse_bind_cols in `src/datashield_mcp/server.py`:
```python


# Conditional Operations
@mcp.tool()
def tidyverse_if_else(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    condition: str,
    true_value: str,
    false_value: str,
    missing_value: str | None = None,
    newobj: str = "",
) -> dict[str, list[str]]:
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
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    
    TidyverseClient(dscontext).if_else(
        condition=condition,
        true_value=true_value,
        false_value=false_value,
        missing_value=missing_value,
        newobj=newobj
    )
    
    return dscontext.session.ls()


@mcp.tool()
def tidyverse_case_when(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    cases: str,
    newobj: str,
) -> dict[str, list[str]]:
    """Create a conditional vector using multi-way case logic in a DataSHIELD session

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        cases: Case expressions in the form "condition ~ value, condition ~ value, ..."
              (e.g., "mpg > 25 ~ 'excellent', mpg > 20 ~ 'good', TRUE ~ 'average'")
        newobj: Name for the new conditional vector

    Returns:
        A dictionary mapping server names to lists of available symbols after operation

    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    
    TidyverseClient(dscontext).case_when(
        cases=cases,
        newobj=newobj
    )
    
    return dscontext.session.ls()


# Tibble Operations
@mcp.tool()
def tibble_as_tibble(
    ctx: Context[ServerSession, AppContext],
    session_id: str,
    df_name: str,
    newobj: str,
) -> dict[str, list[str]]:
    """Convert a DataSHIELD data frame to a tibble

    Args:
        ctx: The MCP tool context, which provides access to the application context and session information
        session_id: The session ID of the connected DataSHIELD session
        df_name: Name of server-side data frame to convert
        newobj: Name for the new tibble

    Returns:
        A dictionary mapping server names to lists of available symbols after conversion

    Raises:
        ValueError: If the session ID is invalid or not connected to DataSHIELD
    """
    dscontext = ctx.request_context.lifespan_context.sessions.get(session_id)
    if not dscontext or not dscontext.session:
        raise ValueError("Not connected to DataSHIELD")
    
    TibbleClient(dscontext).as_tibble(
        df_name=df_name,
        newobj=newobj
    )
    
    return dscontext.session.ls()
```

- [ ] **Step 2: Add tests for conditional and tibble tools**

Add to `tests/test_server_tidyverse.py`:
```python
from datashield_mcp.server import (
    tidyverse_if_else,
    tidyverse_case_when,
    tibble_as_tibble,
)


def test_tidyverse_if_else():
    """Test tidyverse_if_else tool calls TidyverseClient.if_else."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tidyverse_if_else(
        ctx=mock_ctx,
        session_id="test-session",
        condition="mpg > 20",
        true_value="'high'",
        false_value="'low'",
        newobj="mpg_category"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_if_else_with_missing():
    """Test tidyverse_if_else with missing_value parameter."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tidyverse_if_else(
        ctx=mock_ctx,
        session_id="test-session",
        condition="mpg > 20",
        true_value="1",
        false_value="0",
        missing_value="NA",
        newobj="mpg_flag"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_case_when():
    """Test tidyverse_case_when tool calls TidyverseClient.case_when."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tidyverse_case_when(
        ctx=mock_ctx,
        session_id="test-session",
        cases="mpg > 25 ~ 'excellent', mpg > 20 ~ 'good', TRUE ~ 'average'",
        newobj="mpg_rating"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tibble_as_tibble():
    """Test tibble_as_tibble tool calls TibbleClient.as_tibble."""
    mock_ctx, mock_dscontext = create_mock_context()
    
    result = tibble_as_tibble(
        ctx=mock_ctx,
        session_id="test-session",
        df_name="mtcars",
        newobj="mtcars_tibble"
    )
    
    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()
```

- [ ] **Step 3: Run all tests to verify complete implementation**

```bash
cd /home/yannick/projects/datashield-mcp
pytest tests/test_server_tidyverse.py -v
```

Expected: 18 tests pass (14 from previous tasks + 4 new)

- [ ] **Step 4: Run full test suite to check for regressions**

```bash
cd /home/yannick/projects/datashield-mcp
pytest tests/ -v
```

Expected: All tests pass (tidyverse tests + any existing tests)

- [ ] **Step 5: Commit**

```bash
cd /home/yannick/projects/datashield-mcp
git add src/datashield_mcp/server.py tests/test_server_tidyverse.py
git commit -m "feat(mcp): add conditional tools (if_else, case_when) and tibble conversion tool"
```

---

## Task 6: Verify MCP Tool Registration

**Files:**
- No file changes

- [ ] **Step 1: Start the MCP server in dev mode**

```bash
cd /home/yannick/projects/datashield-mcp
make run-dev
```

Expected: Server starts without errors on http://localhost:6274/

- [ ] **Step 2: Check tool list in web interface**

Open browser to http://localhost:6274/ and verify that all 15 new tidyverse tools appear in the tool list:
- tidyverse_select
- tidyverse_filter
- tidyverse_mutate
- tidyverse_arrange
- tidyverse_rename
- tidyverse_slice
- tidyverse_group_by
- tidyverse_ungroup
- tidyverse_group_keys
- tidyverse_distinct
- tidyverse_bind_rows
- tidyverse_bind_cols
- tidyverse_if_else
- tidyverse_case_when
- tibble_as_tibble

- [ ] **Step 3: Stop the server**

Press Ctrl+C in the terminal to stop the server

- [ ] **Step 4: Verify with OpenCode MCP list**

```bash
cd /home/yannick/projects/datashield-mcp
opencode mcp list
```

Expected: Output shows datashield MCP server with 15 new tidyverse tools listed

---

## Success Criteria

All tasks completed when:
- ✅ All 15 tidyverse tools implemented in `server.py`
- ✅ Import statement added for TidyverseClient and TibbleClient
- ✅ 18 unit tests created and passing in `tests/test_server_tidyverse.py`
- ✅ No regressions in existing tests
- ✅ Tools visible in MCP server web interface
- ✅ Tools discoverable via OpenCode MCP list
- ✅ All commits follow conventional commit format
- ✅ Code follows existing patterns in `server.py`
