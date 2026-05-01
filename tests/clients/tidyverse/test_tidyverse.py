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


def test_mutate_new_column(mock_dscontext):
    """Test creating a new column with mutate."""
    client = TidyverseClient(mock_dscontext)
    
    client.mutate(
        df_name="mtcars",
        tidy_expr="mpg_squared = mpg ^ 2",
        newobj="mutated"
    )
    
    # Verify assign was called
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    # Check that newobj and call expression are correct
    assert call_args[0][0] == "mutated"
    call_expr = call_args[0][1]
    assert "mutateDS" in call_expr
    assert "mtcars" in call_expr


def test_mutate_modify_column(mock_dscontext):
    """Test modifying an existing column with mutate."""
    client = TidyverseClient(mock_dscontext)
    
    client.mutate(
        df_name="mtcars",
        tidy_expr="mpg = mpg * 1.6",
        newobj="converted"
    )
    
    # Verify assign was called
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    call_expr = call_args[0][1]
    assert "mutateDS" in call_expr
    assert "mtcars" in call_expr


def test_mutate_multiple_columns(mock_dscontext):
    """Test creating multiple columns in one mutate call."""
    client = TidyverseClient(mock_dscontext)
    
    client.mutate(
        df_name="mtcars",
        tidy_expr="mpg_kml = mpg * 0.425, hp_kw = hp * 0.746",
        newobj="multi_mutate"
    )
    
    # Verify assign was called
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    call_expr = call_args[0][1]
    assert "mutateDS" in call_expr


def test_arrange_single_column(mock_dscontext):
    """Test arranging by a single column."""
    client = TidyverseClient(mock_dscontext)
    
    client.arrange(
        df_name="mtcars",
        tidy_expr="mpg",
        newobj="sorted"
    )
    
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    assert call_args[0][0] == "sorted"
    call_expr = call_args[0][1]
    assert "arrangeDS" in call_expr
    assert "mtcars" in call_expr


def test_arrange_multiple_columns(mock_dscontext):
    """Test arranging by multiple columns with desc()."""
    client = TidyverseClient(mock_dscontext)
    
    client.arrange(
        df_name="mtcars",
        tidy_expr="desc(mpg), cyl",
        newobj="sorted"
    )
    
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    call_expr = call_args[0][1]
    assert "arrangeDS" in call_expr


def test_rename_single_column(mock_dscontext):
    """Test renaming a single column."""
    client = TidyverseClient(mock_dscontext)
    
    client.rename(
        df_name="mtcars",
        tidy_expr="miles_per_gallon = mpg",
        newobj="renamed"
    )
    
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    assert call_args[0][0] == "renamed"
    call_expr = call_args[0][1]
    assert "renameDS" in call_expr
    assert "mtcars" in call_expr


def test_rename_multiple_columns(mock_dscontext):
    """Test renaming multiple columns."""
    client = TidyverseClient(mock_dscontext)
    
    client.rename(
        df_name="mtcars",
        tidy_expr="miles_per_gallon = mpg, cylinders = cyl",
        newobj="renamed"
    )
    
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    call_expr = call_args[0][1]
    assert "renameDS" in call_expr


def test_slice_basic(mock_dscontext):
    """Test slicing rows by position."""
    client = TidyverseClient(mock_dscontext)
    
    client.slice(
        df_name="mtcars",
        tidy_expr="1, 5, 10",
        newobj="sliced"
    )
    
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    assert call_args[0][0] == "sliced"
    call_expr = call_args[0][1]
    assert "sliceDS" in call_expr
    assert "mtcars" in call_expr


def test_slice_range(mock_dscontext):
    """Test slicing with a range."""
    client = TidyverseClient(mock_dscontext)
    
    client.slice(
        df_name="mtcars",
        tidy_expr="1:10",
        newobj="sliced"
    )
    
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    call_expr = call_args[0][1]
    assert "sliceDS" in call_expr


def test_group_by_single_column(mock_dscontext):
    """Test grouping by a single column."""
    client = TidyverseClient(mock_dscontext)
    
    client.group_by(
        df_name="mtcars",
        tidy_expr="cyl",
        newobj="grouped"
    )
    
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    assert call_args[0][0] == "grouped"
    call_expr = call_args[0][1]
    assert "groupByDS" in call_expr
    assert "mtcars" in call_expr


def test_group_by_multiple_columns(mock_dscontext):
    """Test grouping by multiple columns."""
    client = TidyverseClient(mock_dscontext)
    
    client.group_by(
        df_name="mtcars",
        tidy_expr="cyl, gear",
        newobj="grouped"
    )
    
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    call_expr = call_args[0][1]
    assert "groupByDS" in call_expr


def test_ungroup(mock_dscontext):
    """Test ungrouping a grouped dataframe."""
    client = TidyverseClient(mock_dscontext)
    
    client.ungroup(
        df_name="grouped_mtcars",
        newobj="ungrouped"
    )
    
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    assert call_args[0][0] == "ungrouped"
    call_expr = call_args[0][1]
    assert "ungroupDS" in call_expr
    assert "grouped_mtcars" in call_expr


def test_group_keys(mock_dscontext):
    """Test getting group keys from a grouped dataframe."""
    client = TidyverseClient(mock_dscontext)
    
    client.group_keys(
        df_name="grouped_mtcars",
        newobj="keys"
    )
    
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    assert call_args[0][0] == "keys"
    call_expr = call_args[0][1]
    assert "groupKeysDS" in call_expr
    assert "grouped_mtcars" in call_expr


def test_distinct_all_columns(mock_dscontext):
    """Test getting distinct rows across all columns."""
    client = TidyverseClient(mock_dscontext)
    
    client.distinct(
        df_name="mtcars",
        tidy_expr=None,
        newobj="unique"
    )
    
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    assert call_args[0][0] == "unique"
    call_expr = call_args[0][1]
    assert "distinctDS" in call_expr
    assert "mtcars" in call_expr


def test_distinct_specific_columns(mock_dscontext):
    """Test getting distinct rows for specific columns."""
    client = TidyverseClient(mock_dscontext)
    
    client.distinct(
        df_name="mtcars",
        tidy_expr="cyl, gear",
        newobj="unique"
    )
    
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    call_expr = call_args[0][1]
    assert "distinctDS" in call_expr


def test_bind_rows(mock_dscontext):
    """Test binding rows from multiple dataframes."""
    client = TidyverseClient(mock_dscontext)
    
    client.bind_rows(
        df_names=["df1", "df2", "df3"],
        newobj="combined"
    )
    
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    assert call_args[0][0] == "combined"
    call_expr = call_args[0][1]
    assert "bindRowsDS" in call_expr
    assert "df1" in call_expr
    assert "df2" in call_expr
    assert "df3" in call_expr


def test_bind_cols(mock_dscontext):
    """Test binding columns from multiple dataframes."""
    client = TidyverseClient(mock_dscontext)
    
    client.bind_cols(
        df_names=["df1", "df2"],
        newobj="combined"
    )
    
    mock_dscontext.session.assign.assert_called_once()
    call_args = mock_dscontext.session.assign.call_args
    
    assert call_args[0][0] == "combined"
    call_expr = call_args[0][1]
    assert "bindColsDS" in call_expr
    assert "df1" in call_expr
    assert "df2" in call_expr
