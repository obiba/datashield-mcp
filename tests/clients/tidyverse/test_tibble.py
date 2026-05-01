"""Tests for TibbleClient."""
from unittest.mock import MagicMock
import pytest

from datashield_mcp.models import DSContext
from datashield_mcp.clients.tidyverse.tibble import TibbleClient


@pytest.fixture
def mock_dscontext():
    """Create a mock DSContext for testing."""
    context = MagicMock(spec=DSContext)
    context.id = "test-session"
    context.session = MagicMock()
    return context


def test_tibble_client_init(mock_dscontext):
    """Test that TibbleClient can be instantiated."""
    client = TibbleClient(mock_dscontext)
    assert client.dscontext == mock_dscontext


def test_as_tibble_from_dataframe(mock_dscontext):
    """Test converting a dataframe to a tibble."""
    client = TibbleClient(mock_dscontext)
    
    client.as_tibble(
        df_name="mtcars",
        newobj="mtcars_tibble"
    )
    
    # Verify assign was called
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    # Check that newobj and call expression are correct
    assert call_args[0][0] == "mtcars_tibble"
    call_expr = call_args[0][1]
    assert "asTibbleDS" in call_expr
    assert "mtcars" in call_expr
