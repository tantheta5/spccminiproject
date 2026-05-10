"""
macroprocessor.py — Two-pass macroprocessor for MiniMacro.

Pass 1: Build MNT and MDT from source; produce intermediate program.
        Formal parameters (@X, @Y, …) are replaced with positional
        notation (#1, #2, …) in the MDT entries.
        An ALA_DEF is built for each macro definition recording the
        positional-to-formal mapping.

Pass 2: Expand every macro call using MNT, MDT, and ALA_EXP.
        A single combined ALA_EXP accumulates the argument bindings
        for every macro call encountered.
"""

from tables import MNT, MDT, ALA_DEF, ALA_EXP
from parser import parse_line, is_macro_def, is_mend, extract_macro_name_and_params


# ------------------------------------------------------------------ #
#  Pass 1 — build macro tables and strip definitions from source
# ------------------------------------------------------------------ #

def pass1(source_lines):
    """Scan *source_lines*, populate MNT / MDT, and return
    (mnt, mdt, ala_defs, intermediate_program).

    ala_defs: dict {macro_name -> ALA_DEF} for display purposes.
    Raises RuntimeError on missing MACROEND.
    """
    mnt = MNT()
    mdt = MDT()
    ala_defs = {}          # macro_name -> ALA_DEF
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

            # Build ALA_DEF for this macro
            ala_def = ALA_DEF()
            formal_to_pos = {}          # @X -> #1
            for idx, formal in enumerate(params, start=1):
                pos_token = f"#{idx}"
                ala_def.add(pos_token, formal)
                formal_to_pos[formal] = pos_token
            ala_defs[macro_name] = ala_def

            mdt_start = mdt.size()      # index where this body starts
            mnt.add(macro_name, mdt_start, len(params))

            # Store header line in MDT with positional notation
            header_positional = _replace_formals(header.strip(), formal_to_pos)
            mdt.add(header_positional)

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

                # Replace formal params with positional notation in body lines
                body_positional = _replace_formals(body_line.strip(), formal_to_pos)
                mdt.add(body_positional)

                # Register nested macro definition in MNT
                if is_macro_def(body_tokens) and (i + 1) < len(source_lines):
                    nested_header = source_lines[i + 1].rstrip("\n")
                    n_name, n_params = extract_macro_name_and_params(nested_header)
                    nested_mdt_start = mdt.size()
                    mnt.add(n_name, nested_mdt_start, len(n_params))

                    # Build ALA_DEF for nested macro
                    n_ala_def = ALA_DEF()
                    for ni, nf in enumerate(n_params, start=1):
                        n_ala_def.add(f"#{ni}", nf)
                    ala_defs[n_name] = n_ala_def

                i += 1
        else:
            intermediate.append(line)
            i += 1

    return mnt, mdt, ala_defs, intermediate


def _replace_formals(line, formal_to_pos):
    """Replace every formal parameter token (@X, @Y, …) in *line* with
    its corresponding positional token (#1, #2, …)."""
    result = line
    for formal, pos in formal_to_pos.items():
        result = result.replace(formal, pos)
    return result


# ------------------------------------------------------------------ #
#  Pass 2 — expand macro calls in the intermediate program
# ------------------------------------------------------------------ #

def pass2(intermediate, mnt, mdt):
    """Expand all macro calls in the intermediate program and return
    (expanded_lines, ala_exp).

    ala_exp is a combined ALA_EXP that records every macro call's
    argument bindings in order.

    Raises RuntimeError on undefined macros or argument-count mismatches.
    """
    # Opcodes that are part of the MiniMacro language itself (not macro calls)
    KNOWN_DIRECTIVES = {
        "BEGIN_CODE", "END_CODE", "MINIMACRO", "MACROEND",
        # common pseudo-instructions that are valid plain instructions:
        "PULL_VAL", "PUSH_VAL", "ADD_VAL", "MUL_VAL", "SUB_VAL", "DIV_VAL",
        "STORE_TMP", "PULL_TMP", "STORE_VAR", "LOAD_CONST", "PUSH_ALL",
        "CMP_MIN", "CMP_MAX", "STORE_IF_LT", "STORE_IF_GT",
        "LOAD_VAL", "STORE_VAL", "NOP", "HALT",
    }

    ala_exp = ALA_EXP()
    expanded = []

    for line in intermediate:
        tokens = parse_line(line)
        if not tokens:
            expanded.append(line)
            continue

        opcode = tokens[0]

        # Skip comment lines (starting with ';')
        if opcode.startswith(";"):
            expanded.append(line)
            continue

        entry = mnt.lookup(opcode)

        if entry is not None:
            # --- macro call detected ---
            actual_args = tokens[1:] if len(tokens) > 1 else []
            # Split further if arguments are comma-separated in a single token
            if len(actual_args) == 1 and "," in actual_args[0]:
                actual_args = [a.strip() for a in actual_args[0].split(",")]

            expanded_lines = _expand_macro(opcode, actual_args, mnt, mdt, ala_exp)
            expanded.extend(expanded_lines)
        else:
            # Check if opcode looks like an undefined macro call:
            # all uppercase, not a known directive, and has at least one argument
            if (
                opcode.isupper()
                and opcode not in KNOWN_DIRECTIVES
                and len(tokens) > 1
            ):
                raise RuntimeError(f"Undefined macro: '{opcode}'")
            expanded.append(line)

    return expanded, ala_exp


def _expand_macro(macro_name, actual_args, mnt, mdt, ala_exp, depth=0):
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

    # --- Record this call in the combined ALA_EXP ---
    ala_exp.record_call(macro_name, actual_args)

    # Build a positional-to-actual mapping for substitution: #1 -> A, etc.
    pos_to_actual = ala_exp.get_latest_bindings()   # {#1: actual, …}

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

        # Skip lines inside a nested definition
        if nest_level > 0:
            idx += 1
            continue

        # Substitute #1, #2, … with actual arguments
        substituted = _substitute_positional(mdt_line, pos_to_actual)
        sub_tokens = parse_line(substituted)

        # Check if the substituted line is itself a macro call
        if sub_tokens and mnt.lookup(sub_tokens[0]) is not None:
            inner_name = sub_tokens[0]
            inner_args = sub_tokens[1:] if len(sub_tokens) > 1 else []
            if len(inner_args) == 1 and "," in inner_args[0]:
                inner_args = [a.strip() for a in inner_args[0].split(",")]
            result.extend(
                _expand_macro(inner_name, inner_args, mnt, mdt, ala_exp, depth + 1)
            )
        else:
            result.append(substituted)

        idx += 1

    return result


def _substitute_positional(line, pos_to_actual):
    """Replace #1, #2, … tokens in *line* with their actual arguments."""
    # Sort by length descending to avoid #1 matching inside #10, #11, etc.
    result = line
    for pos in sorted(pos_to_actual.keys(), key=len, reverse=True):
        result = result.replace(pos, pos_to_actual[pos])
    return result
