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

    # ---- Pass 1 — build tables ----
    try:
        mnt, mdt, intermediate = pass1(source_lines)
    except RuntimeError as e:
        print(f"\n[Pass 1 Error] {e}")
        sys.exit(1)

    mnt.display()
    mdt.display()

    print("Intermediate Program (after Pass 1)")
    print("-" * 40)
    for line in intermediate:
        if line.strip():
            print(f"  {line}")
    print()

    # ---- Pass 2 — expand macro calls ----
    try:
        expanded, ala = pass2(intermediate, mnt, mdt)
    except RuntimeError as e:
        print(f"\n[Pass 2 Error] {e}")
        sys.exit(1)

    ala.display()

    print("Expanded Program")
    print("-" * 40)
    for line in expanded:
        if line.strip():
            print(f"  {line}")
    print()

    # ---- Write output ----
    write_output([l for l in expanded if l.strip()], output_file)
    print(f"Expanded program written to: {output_file}")


if __name__ == "__main__":
    main()
