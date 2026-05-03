"""
macroprocessor.py — Two-pass macroprocessor for MiniMacro.

Pass 1: Build MNT and MDT from source; produce intermediate program.
Pass 2: Expand every macro call using MNT, MDT, and ALA.
"""

from tables import MNT, MDT, ALA
from parser import parse_line, is_macro_def, is_mend, extract_macro_name_and_params


# ------------------------------------------------------------------ #
#  Pass 1 — build macro tables and strip definitions from source
# ------------------------------------------------------------------ #

def pass1(source_lines):
    """Scan *source_lines*, populate MNT / MDT, and return
    (mnt, mdt, intermediate_program).

    Raises RuntimeError on missing MACROEND.
    """
    mnt = MNT()
    mdt = MDT()
    intermediate = []

    i = 0
    while i < len(source_lines):
        line = source_lines[i].rstrip("\n")
        tokens = parse_line(line)

        if is_macro_def(tokens):
            # --- start of a macro definition ---
            i += 1
            if i >= len(source_lines):
                raise RuntimeError("Missing macro header after MINIMACRO keyword.")

            header = source_lines[i].rstrip("\n")
            macro_name, params = extract_macro_name_and_params(header)

            mdt_start = mdt.size()          # index where this body starts
            mnt.add(macro_name, mdt_start, len(params))

            # Store header line in MDT (useful for nested macro display)
            mdt.add(header.strip())

            i += 1
            nest_level = 1

            while nest_level > 0:
                if i >= len(source_lines):
                    raise RuntimeError(
                        f"Missing MACROEND in macro definition for '{macro_name}'."
                    )
                body_line = source_lines[i].rstrip("\n")
                body_tokens = parse_line(body_line)

                if is_macro_def(body_tokens):
                    nest_level += 1

                if is_mend(body_tokens):
                    nest_level -= 1

                # Store every line (including nested MACRO/MEND) in MDT
                mdt.add(body_line.strip())

                # If we just found a nested macro header (line after MACRO),
                # register it in MNT as well so Pass 2 can find it.
                if is_macro_def(body_tokens) and (i + 1) < len(source_lines):
                    nested_header = source_lines[i + 1].rstrip("\n")
                    n_name, n_params = extract_macro_name_and_params(nested_header)
                    # MDT index for nested macro = current mdt size (it will
                    # be added on the next iteration)
                    nested_mdt_start = mdt.size()
                    mnt.add(n_name, nested_mdt_start, len(n_params))

                i += 1
        else:
            intermediate.append(line)
            i += 1

    return mnt, mdt, intermediate


# ------------------------------------------------------------------ #
#  Pass 2 — expand macro calls in the intermediate program
# ------------------------------------------------------------------ #

def pass2(intermediate, mnt, mdt):
    """Expand all macro calls in the intermediate program and return
    (expanded_lines, ala).

    The ALA object returned contains the mappings from the *last*
    expansion performed (kept for display purposes).

    Raises RuntimeError on undefined macros or argument-count mismatches.
    """
    ala = ALA()
    expanded = []

    for line in intermediate:
        tokens = parse_line(line)
        if not tokens:
            expanded.append(line)
            continue

        opcode = tokens[0]
        entry = mnt.lookup(opcode)

        if entry is not None:
            # --- macro call detected ---
            actual_args = tokens[1:] if len(tokens) > 1 else []
            # Split further if arguments are comma-separated in a single token
            if len(actual_args) == 1 and "," in actual_args[0]:
                actual_args = [a.strip() for a in actual_args[0].split(",")]

            expanded_lines = _expand_macro(opcode, actual_args, mnt, mdt, ala)
            expanded.extend(expanded_lines)
        else:
            expanded.append(line)

    return expanded, ala


def _expand_macro(macro_name, actual_args, mnt, mdt, ala, depth=0):
    """Recursively expand a single macro call and return a list of
    expanded instruction lines."""
    if depth > 50:
        raise RuntimeError("Maximum macro expansion depth exceeded (possible infinite recursion).")

    entry = mnt.lookup(macro_name)
    if entry is None:
        raise RuntimeError(f"Undefined macro: '{macro_name}'")

    expected = entry["param_count"]
    if len(actual_args) != expected:
        raise RuntimeError(
            f"Incorrect number of arguments for macro '{macro_name}': "
            f"expected {expected}, got {len(actual_args)}."
        )

    mdt_start = entry["index"]

    # --- Build ALA for this expansion ---
    ala.clear()
    # The header line in MDT contains the formal params
    header_line = mdt.get(mdt_start)
    _, formal_params = extract_macro_name_and_params(header_line)

    for formal, actual in zip(formal_params, actual_args):
        ala.add(formal, actual)

    # --- Walk the MDT body and substitute / expand ---
    result = []
    idx = mdt_start + 1          # skip the header line
    nest_level = 0

    while idx < mdt.size():
        mdt_line = mdt.get(idx)
        mdt_tokens = parse_line(mdt_line)

        if is_mend(mdt_tokens):
            if nest_level == 0:
                break                # end of this macro's body
            else:
                nest_level -= 1
                idx += 1
                continue

        if is_macro_def(mdt_tokens):
            nest_level += 1
            idx += 1
            continue

        # Skip lines inside a nested definition (they belong to the
        # inner macro and were already registered in Pass 1).
        if nest_level > 0:
            idx += 1
            continue

        # Substitute formal parameters with actual arguments
        substituted = ala.substitute(mdt_line)
        sub_tokens = parse_line(substituted)

        # Check if the substituted line is itself a macro call
        if sub_tokens and mnt.lookup(sub_tokens[0]) is not None:
            inner_name = sub_tokens[0]
            inner_args = sub_tokens[1:] if len(sub_tokens) > 1 else []
            if len(inner_args) == 1 and "," in inner_args[0]:
                inner_args = [a.strip() for a in inner_args[0].split(",")]
            result.extend(
                _expand_macro(inner_name, inner_args, mnt, mdt, ala, depth + 1)
            )
        else:
            result.append(substituted)

        idx += 1

    return result
