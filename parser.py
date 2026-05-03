"""
parser.py — Utility functions for parsing MiniMacro source lines.
"""


def parse_line(line):
    """Split a source line into whitespace-separated tokens."""
    return line.strip().split()


def is_macro_def(tokens):
    """Return True if the token list starts with the MINIMACRO keyword."""
    return len(tokens) > 0 and tokens[0].upper() == "MINIMACRO"


def is_mend(tokens):
    """Return True if the token list starts with the MACROEND keyword."""
    return len(tokens) > 0 and tokens[0].upper() == "MACROEND"


def extract_macro_name_and_params(line):
    """Parse a macro header line such as  'INCR @X,@Y'  and return
    (macro_name, [list_of_formal_params]).

    Parameters in the header are separated by commas and prefixed with '@'.
    """
    tokens = line.strip().split()
    if len(tokens) < 1:
        return None, []

    macro_name = tokens[0]
    params = []

    if len(tokens) > 1:
        # params may be separated by commas and/or spaces
        raw = " ".join(tokens[1:])
        params = [p.strip() for p in raw.split(",") if p.strip()]

    return macro_name, params
