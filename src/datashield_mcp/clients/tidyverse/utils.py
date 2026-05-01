"""Utility functions for tidyverse client operations."""


def get_encode_dictionary() -> dict[str, list[str]]:
    """Generate an encoding dictionary for special characters.

    This encoding is used to pass R expressions through the DataSHIELD
    infrastructure without conflicts with the R parser.

    Returns:
        A dictionary with 'input' and 'output' keys, each containing a list
        of strings representing characters to encode and their encoded forms.
    """
    encode_dict = {
        "input": ["(", ")", '"', ",", " ", "!", "&", "|", "'", "=", "+", "-", "*", "/", "^", ">", "<", "~", "\n", "%"],
        "output": [
            "$LB$",
            "$RB$",
            "$QUOTE$",
            "$COMMA$",
            "$SPACE$",
            "$EXCL$",
            "$AND$",
            "$OR$",
            "$APO$",
            "$EQU$",
            "$ADD$",
            "$SUB$",
            "$MULT$",
            "$DIVIDE$",
            "$POWER$",
            "$GT$",
            "$LT$",
            "$TILDE$",
            "$LINE$",
            "$PCT$",
        ],
    }
    return encode_dict


def encode_tidy_eval(input_string: str) -> str:
    """Encode a tidy evaluation expression string.

    Args:
        input_string: The expression string to encode

    Returns:
        The encoded expression string with special characters replaced
    """
    if not input_string:
        return input_string

    encode_dict = get_encode_dictionary()

    # Create mapping of input chars to output tokens
    encode_map = dict(zip(encode_dict["input"], encode_dict["output"], strict=True))

    # Encode each character
    result = []
    for char in input_string:
        if char in encode_map:
            result.append(encode_map[char])
        else:
            result.append(char)

    return "".join(result)


def make_serverside_call(fun_name: str, tidy_expr: str | None, other_args: list) -> str:
    """Construct a serverside function call string.

    Args:
        fun_name: Name of the serverside DataSHIELD function
        tidy_expr: Encoded tidy expression (can be None)
        other_args: List of additional arguments to pass

    Returns:
        A string representing the R function call
    """
    encoded_expr = encode_tidy_eval(tidy_expr) if tidy_expr is not None else None

    # Build argument list
    args = []
    if encoded_expr is not None:
        args.append(f"'{encoded_expr}'")

    # Add other arguments
    for arg in other_args:
        if arg is None:
            args.append("NULL")
        elif isinstance(arg, bool):
            args.append("TRUE" if arg else "FALSE")
        elif isinstance(arg, str):
            args.append(f"'{arg}'")
        else:
            args.append(str(arg))

    # Construct the call
    args_str = ", ".join(args)
    return f"{fun_name}({args_str})"
