"""Tests for tidyverse utility functions."""
from datashield_mcp.clients.tidyverse.utils import get_encode_dictionary, encode_tidy_eval


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
