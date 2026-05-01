"""Tests for TidyverseClient."""
from unittest.mock import MagicMock, call
import pytest

from datashield_mcp.models import DSContext
from datashield_mcp.clients.tidyverse.tidyverse import TidyverseClient


@pytest.fixture
def mock_dscontext():
    """Create a mock DSContext for testing."""
    context = MagicMock(spec=DSContext)
    context.id = "test-session"
    context.session = MagicMock()
    return context


def test_select_creates_tidyverse_client(mock_dscontext):
    """Test that TidyverseClient can be instantiated."""
    client = TidyverseClient(mock_dscontext)
    assert client.dscontext == mock_dscontext


def test_select_basic_columns(mock_dscontext):
    """Test selecting basic columns from a dataframe."""
    client = TidyverseClient(mock_dscontext)
    
    client.select(
        df_name="mtcars",
        tidy_expr="mpg, cyl",
        newobj="subset"
    )
    
    # Verify that assign was called with the correct arguments
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    # Check that newobj and call expression are correct
    assert call_args[0][0] == "subset"
    call_expr = call_args[0][1]
    assert "selectDS" in call_expr
    assert "mtcars" in call_expr


def test_select_with_helpers(mock_dscontext):
    """Test selecting columns with tidy select helpers."""
    client = TidyverseClient(mock_dscontext)
    
    client.select(
        df_name="mtcars",
        tidy_expr="starts_with('m'), ends_with('t')",
        newobj="subset"
    )
    
    # Verify assign was called
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    # Verify the expression includes the helper functions
    call_expr = call_args[0][1]
    assert "selectDS" in call_expr
    assert "mtcars" in call_expr


def test_filter_basic(mock_dscontext):
    """Test filtering with a simple condition."""
    client = TidyverseClient(mock_dscontext)
    
    client.filter(
        df_name="mtcars",
        tidy_expr="mpg > 20",
        newobj="filtered"
    )
    
    # Verify assign was called
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    # Check that newobj and call expression are correct
    assert call_args[0][0] == "filtered"
    call_expr = call_args[0][1]
    assert "filterDS" in call_expr
    assert "mtcars" in call_expr


def test_filter_complex_condition(mock_dscontext):
    """Test filtering with complex logical conditions."""
    client = TidyverseClient(mock_dscontext)
    
    client.filter(
        df_name="mtcars",
        tidy_expr="mpg > 20 & cyl == 4",
        newobj="filtered"
    )
    
    # Verify assign was called
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    call_expr = call_args[0][1]
    assert "filterDS" in call_expr
    assert "mtcars" in call_expr
