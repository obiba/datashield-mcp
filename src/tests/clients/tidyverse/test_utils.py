"""Tests for tidyverse utility functions."""

import pytest

from datashield_mcp.clients.tidyverse.utils import (
    encode_tidy_eval,
    get_encode_dictionary,
    make_serverside_call,
    validate_symbol_name,
)


def test_get_encode_dictionary():
    """Test that encoding dictionary contains expected mappings."""
    encode_dict = get_encode_dictionary()

    assert "(" in encode_dict["input"]
    assert ")" in encode_dict["input"]
    assert "," in encode_dict["input"]

    assert "$LB$" in encode_dict["output"]
    assert "$RB$" in encode_dict["output"]
    assert "$COMMA$" in encode_dict["output"]

    # Check that input and output lists have same length
    assert len(encode_dict["input"]) == len(encode_dict["output"])


def test_encode_tidy_eval_simple():
    """Test encoding a simple expression."""
    expr = "mpg > 20"
    encoded = encode_tidy_eval(expr)

    # Space should be encoded to $SPACE$, > should be encoded to $GT$
    assert "$SPACE$" in encoded
    assert "$GT$" in encoded
    assert "mpg" in encoded
    assert "20" in encoded


def test_encode_tidy_eval_complex():
    """Test encoding a complex expression with multiple special chars."""
    expr = "filter(df, cyl == 4 & mpg > 20)"
    encoded = encode_tidy_eval(expr)

    # Check that special characters are encoded
    assert "$LB$" in encoded  # (
    assert "$RB$" in encoded  # )
    assert "$COMMA$" in encoded  # ,
    assert "$SPACE$" in encoded  # space
    assert "$EQU$" in encoded  # =
    assert "$AND$" in encoded  # &
    assert "$GT$" in encoded  # >


def test_encode_tidy_eval_preserves_alphanumeric():
    """Test that alphanumeric characters are not encoded."""
    expr = "abc123XYZ"
    encoded = encode_tidy_eval(expr)

    assert encoded == "abc123XYZ"


# ---------------------------------------------------------------------------
# validate_symbol_name
# ---------------------------------------------------------------------------

class TestValidateSymbolName:
    def test_valid_names(self):
        for name in ["D", "ds1", "my.data", "study_data", "A1.b_C"]:
            validate_symbol_name(name)  # must not raise

    def test_rejects_single_quote(self):
        with pytest.raises(ValueError):
            validate_symbol_name("ds'injection")

    def test_rejects_backslash(self):
        with pytest.raises(ValueError):
            validate_symbol_name("ds\\n")

    def test_rejects_starts_with_digit(self):
        with pytest.raises(ValueError):
            validate_symbol_name("1bad")

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError):
            validate_symbol_name("")

    def test_rejects_space(self):
        with pytest.raises(ValueError):
            validate_symbol_name("bad name")

    def test_rejects_semicolon(self):
        with pytest.raises(ValueError):
            validate_symbol_name("bad;name")


# ---------------------------------------------------------------------------
# make_serverside_call – injection guard
# ---------------------------------------------------------------------------

class TestMakeServersideCallInjection:
    def test_valid_df_name(self):
        result = make_serverside_call("selectDS", None, ["myDf"])
        assert result == "selectDS('myDf')"

    def test_raises_on_quote_in_df_name(self):
        with pytest.raises(ValueError):
            make_serverside_call("selectDS", None, ["df'DROP"])

    def test_raises_on_backslash_in_df_name(self):
        with pytest.raises(ValueError):
            make_serverside_call("selectDS", None, ["df\\x"])

    def test_multiple_df_names_all_validated(self):
        # first name valid, second name invalid
        with pytest.raises(ValueError):
            make_serverside_call("bindRowsDS", None, ["good", "bad'name"])
