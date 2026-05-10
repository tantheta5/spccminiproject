"""
main.py — Entry point for the MiniMacro macroprocessor.

Usage:
    python main.py input/sample_program.txt
"""

import sys
import os
from macroprocessor import pass1, pass2


def read_source(filepath):
    """Read the source file and return its lines."""
    if not os.path.isfile(filepath):
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
    with open(filepath, "r") as f:
        return f.readlines()


def write_output(lines, filepath):
    """Write the expanded program to the output file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        for line in lines:
            f.write(line + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <source_file>")
        print("Example: python main.py input/sample_program.txt")
        sys.exit(1)

    source_file = sys.argv[1]
    output_file = os.path.join("output", "expanded_program.txt")

    # ---- Read source ----
    source_lines = read_source(source_file)
    print(f"Reading source file: {source_file}")
    print("=" * 50)

    # ---------------------------------------------------------------- #
    # PASS 1 — build MNT, MDT, and definition-phase ALA               #
    # ---------------------------------------------------------------- #
    try:
        mnt, mdt, ala_defs, intermediate = pass1(source_lines)
    except RuntimeError as e:
        print(f"\n[Pass 1 Error] {e}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("  PASS 1 — Macro Definition Processing")
    print("=" * 50)

    # MNT
    mnt.display()

    # MDT
    mdt.display()

    # ALA (Definition phase) — one table per macro defined
    print("ALA — Definition Phase (Formal Parameter Mapping)")
    print("-" * 50)
    if ala_defs:
        for macro_name, ala_def in ala_defs.items():
            print(f"  Macro: {macro_name}")
            print(f"  {'Position':<12} {'Parameter'}")
            print(f"  {'-'*28}")
            for pos, formal in ala_def.entries:
                print(f"  {pos:<12} {formal}")
            print()
    else:
        print("  (no macro definitions found)")
        print()

    # Intermediate program
    print("Intermediate Program (after Pass 1 — definitions removed)")
    print("-" * 50)
    for line in intermediate:
        if line.strip():
            print(f"  {line}")
    print()

    # ---------------------------------------------------------------- #
    # PASS 2 — macro expansion                                         #
    # ---------------------------------------------------------------- #
    try:
        expanded, ala_exp = pass2(intermediate, mnt, mdt)
    except RuntimeError as e:
        print(f"\n[Pass 2 Error] {e}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("  PASS 2 — Macro Expansion")
    print("=" * 50)

    # Combined ALA (Expansion phase) — all calls in one table
    print("\nALA — Expansion Phase (All Macro Call Argument Bindings)")
    print("-" * 50)
    if ala_exp.calls:
        for label, bindings in ala_exp.calls:
            print(f"  Call: {label}")
            print(f"  {'Position':<12} {'Actual Argument'}")
            print(f"  {'-'*30}")
            for pos, arg in bindings:
                print(f"  {pos:<12} {arg}")
            print()
    else:
        print("  (no macro calls found)")
        print()

    # Final expanded program
    print("Final Expanded Program")
    print("-" * 50)
    for line in expanded:
        if line.strip():
            print(f"  {line}")
    print()

    # ---- Write output ----
    write_output([l for l in expanded if l.strip()], output_file)
    print(f"Expanded program written to: {output_file}")


if __name__ == "__main__":
    main()
