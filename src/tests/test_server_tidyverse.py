"""Tests for tidyverse MCP tools."""

from unittest.mock import MagicMock, patch
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
    tidyverse_distinct,
    tidyverse_bind_rows,
    tidyverse_bind_cols,
    tidyverse_if_else,
    tidyverse_case_when,
    tibble_as_tibble,
)


def create_mock_context(session_id: str = "test-session"):
    """Helper to create a mock MCP context with DSContext."""
    mock_session = MagicMock()
    mock_session.ls.return_value = {"server1": ["mtcars", "subset"]}

    mock_dscontext = MagicMock()
    mock_dscontext.session = mock_session

    mock_ctx = MagicMock()
    mock_ctx.request_context.lifespan_context.sessions = {session_id: mock_dscontext}

    return mock_ctx, mock_dscontext


def assert_tool_invokes_client_method(
    mock_client_cls,
    mock_dscontext,
    method_name: str,
    *,
    use_session: bool = True,
    **expected_kwargs,
):
    """Assert that a tool instantiated the right client and invoked the expected method."""
    client_context = mock_dscontext.session if use_session else mock_dscontext
    mock_client_cls.assert_called_once_with(client_context)
    method = getattr(mock_client_cls.return_value, method_name)
    method.assert_called_once_with(**expected_kwargs)


def test_tidyverse_select():
    """Test tidyverse_select tool calls TidyverseClient.select."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TidyverseClient") as mock_client_cls:
        result = tidyverse_select(
            ctx=mock_ctx, session_id="test-session", df_name="mtcars", tidy_expr="mpg, cyl", newobj="subset"
        )

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "select",
        df_name="mtcars",
        tidy_expr="mpg, cyl",
        newobj="subset",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_filter():
    """Test tidyverse_filter tool calls TidyverseClient.filter."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TidyverseClient") as mock_client_cls:
        result = tidyverse_filter(
            ctx=mock_ctx, session_id="test-session", df_name="mtcars", tidy_expr="mpg > 20", newobj="filtered"
        )

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "filter",
        df_name="mtcars",
        tidy_expr="mpg > 20",
        newobj="filtered",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_if_else():
    """Test tidyverse_if_else tool calls TidyverseClient.if_else."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TidyverseClient") as mock_client_cls:
        result = tidyverse_if_else(
            ctx=mock_ctx,
            session_id="test-session",
            condition="mpg > 20",
            true_value="'high'",
            false_value="'low'",
            newobj="mpg_category",
        )

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "if_else",
        condition="mpg > 20",
        true_value="'high'",
        false_value="'low'",
        missing_value=None,
        newobj="mpg_category",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_if_else_with_missing():
    """Test tidyverse_if_else with missing_value parameter."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TidyverseClient") as mock_client_cls:
        result = tidyverse_if_else(
            ctx=mock_ctx,
            session_id="test-session",
            condition="mpg > 20",
            true_value="1",
            false_value="0",
            missing_value="NA",
            newobj="mpg_flag",
        )

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "if_else",
        condition="mpg > 20",
        true_value="1",
        false_value="0",
        missing_value="NA",
        newobj="mpg_flag",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_if_else_requires_newobj():
    """Test tidyverse_if_else requires newobj argument."""
    mock_ctx, _ = create_mock_context()

    with pytest.raises(TypeError):
        tidyverse_if_else(
            ctx=mock_ctx,
            session_id="test-session",
            condition="mpg > 20",
            true_value="'high'",
            false_value="'low'",
        )


def test_tidyverse_case_when():
    """Test tidyverse_case_when tool calls TidyverseClient.case_when."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TidyverseClient") as mock_client_cls:
        result = tidyverse_case_when(
            ctx=mock_ctx,
            session_id="test-session",
            cases="mpg > 25 ~ 'excellent', mpg > 20 ~ 'good', TRUE ~ 'average'",
            newobj="mpg_rating",
        )

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "case_when",
        cases="mpg > 25 ~ 'excellent', mpg > 20 ~ 'good', TRUE ~ 'average'",
        newobj="mpg_rating",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tibble_as_tibble():
    """Test tibble_as_tibble tool calls TibbleClient.as_tibble."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TibbleClient") as mock_client_cls:
        result = tibble_as_tibble(ctx=mock_ctx, session_id="test-session", df_name="mtcars", newobj="mtcars_tibble")

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "as_tibble",
        df_name="mtcars",
        newobj="mtcars_tibble",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_distinct():
    """Test tidyverse_distinct tool calls TidyverseClient.distinct."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TidyverseClient") as mock_client_cls:
        result = tidyverse_distinct(
            ctx=mock_ctx, session_id="test-session", df_name="mtcars", tidy_expr="cyl, gear", newobj="unique"
        )

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "distinct",
        df_name="mtcars",
        tidy_expr="cyl, gear",
        newobj="unique",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_distinct_all_columns():
    """Test tidyverse_distinct with None (all columns)."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TidyverseClient") as mock_client_cls:
        result = tidyverse_distinct(
            ctx=mock_ctx, session_id="test-session", df_name="mtcars", tidy_expr=None, newobj="unique"
        )

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "distinct",
        df_name="mtcars",
        tidy_expr=None,
        newobj="unique",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_bind_rows():
    """Test tidyverse_bind_rows tool calls TidyverseClient.bind_rows."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TidyverseClient") as mock_client_cls:
        result = tidyverse_bind_rows(
            ctx=mock_ctx, session_id="test-session", df_names=["df1", "df2", "df3"], newobj="combined"
        )

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "bind_rows",
        df_names=["df1", "df2", "df3"],
        newobj="combined",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_bind_cols():
    """Test tidyverse_bind_cols tool calls TidyverseClient.bind_cols."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TidyverseClient") as mock_client_cls:
        result = tidyverse_bind_cols(
            ctx=mock_ctx, session_id="test-session", df_names=["df1", "df2"], newobj="combined"
        )

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "bind_cols",
        df_names=["df1", "df2"],
        newobj="combined",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_group_by():
    """Test tidyverse_group_by tool calls TidyverseClient.group_by."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TidyverseClient") as mock_client_cls:
        result = tidyverse_group_by(
            ctx=mock_ctx, session_id="test-session", df_name="mtcars", tidy_expr="cyl, gear", newobj="grouped"
        )

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "group_by",
        df_name="mtcars",
        tidy_expr="cyl, gear",
        newobj="grouped",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_ungroup():
    """Test tidyverse_ungroup tool calls TidyverseClient.ungroup."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TidyverseClient") as mock_client_cls:
        result = tidyverse_ungroup(
            ctx=mock_ctx, session_id="test-session", df_name="grouped_mtcars", newobj="ungrouped"
        )

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "ungroup",
        df_name="grouped_mtcars",
        newobj="ungrouped",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_group_keys():
    """Test tidyverse_group_keys tool calls TidyverseClient.group_keys."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TidyverseClient") as mock_client_cls:
        result = tidyverse_group_keys(ctx=mock_ctx, session_id="test-session", df_name="grouped_mtcars", newobj="keys")

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "group_keys",
        df_name="grouped_mtcars",
        newobj="keys",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_tool_invalid_session():
    """Test error handling for invalid session ID."""
    mock_ctx = MagicMock()
    mock_ctx.request_context.lifespan_context.sessions = {}

    with pytest.raises(ValueError, match="Not connected to DataSHIELD"):
        tidyverse_select(ctx=mock_ctx, session_id="invalid-session", df_name="mtcars", tidy_expr="mpg", newobj="subset")


def test_tidyverse_mutate():
    """Test tidyverse_mutate tool calls TidyverseClient.mutate."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TidyverseClient") as mock_client_cls:
        result = tidyverse_mutate(
            ctx=mock_ctx,
            session_id="test-session",
            df_name="mtcars",
            tidy_expr="mpg_squared = mpg ^ 2",
            newobj="mutated",
        )

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "mutate",
        df_name="mtcars",
        tidy_expr="mpg_squared = mpg ^ 2",
        newobj="mutated",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_arrange():
    """Test tidyverse_arrange tool calls TidyverseClient.arrange."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TidyverseClient") as mock_client_cls:
        result = tidyverse_arrange(
            ctx=mock_ctx, session_id="test-session", df_name="mtcars", tidy_expr="desc(mpg)", newobj="sorted"
        )

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "arrange",
        df_name="mtcars",
        tidy_expr="desc(mpg)",
        newobj="sorted",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_rename():
    """Test tidyverse_rename tool calls TidyverseClient.rename."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TidyverseClient") as mock_client_cls:
        result = tidyverse_rename(
            ctx=mock_ctx,
            session_id="test-session",
            df_name="mtcars",
            tidy_expr="miles_per_gallon = mpg",
            newobj="renamed",
        )

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "rename",
        df_name="mtcars",
        tidy_expr="miles_per_gallon = mpg",
        newobj="renamed",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()


def test_tidyverse_slice():
    """Test tidyverse_slice tool calls TidyverseClient.slice."""
    mock_ctx, mock_dscontext = create_mock_context()

    with patch("datashield_mcp.server.TidyverseClient") as mock_client_cls:
        result = tidyverse_slice(
            ctx=mock_ctx, session_id="test-session", df_name="mtcars", tidy_expr="1:10", newobj="sliced"
        )

    assert_tool_invokes_client_method(
        mock_client_cls,
        mock_dscontext,
        "slice",
        df_name="mtcars",
        tidy_expr="1:10",
        newobj="sliced",
    )

    assert result == {"server1": ["mtcars", "subset"]}
    mock_dscontext.session.ls.assert_called_once()
