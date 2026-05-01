"""Tests for tidyverse MCP tools."""
from unittest.mock import MagicMock
import pytest

from datashield_mcp.server import (
    tidyverse_select,
    tidyverse_filter,
    tidyverse_mutate,
    tidyverse_arrange,
    tidyverse_rename,
    tidyverse_slice,
    tidyverse_group_by,
    tidyverse_ungroup,
    tidyverse_group_keys,
)


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

