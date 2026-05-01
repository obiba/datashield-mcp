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
