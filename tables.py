"""
tables.py — Data structures for the MiniMacro macroprocessor.

MNT  (Macro Name Table)   — macro name → (MDT start index, param count)
MDT  (Macro Definition Table) — sequential list of macro body lines
ALA  (Argument List Array)    — formal parameter → actual argument mapping
"""


class MNT:
    """Macro Name Table — stores each macro's name, MDT start index,
    and number of formal parameters."""

    def __init__(self):
        # name -> {"index": int, "param_count": int}
        self.table = {}

    def add(self, name, mdt_index, param_count):
        self.table[name] = {"index": mdt_index, "param_count": param_count}

    def lookup(self, name):
        return self.table.get(name)

    def display(self):
        print("\nMNT (Macro Name Table)")
        print("-" * 40)
        print(f"{'Macro Name':<15} {'MDT Index':<12} {'#Params'}")
        print("-" * 40)
        for name, info in self.table.items():
            print(f"{name:<15} {info['index']:<12} {info['param_count']}")
        print()


class MDT:
    """Macro Definition Table — stores the body of every macro definition
    as a flat, sequentially-indexed list of instruction lines."""

    def __init__(self):
        self.table = []  # list of instruction strings

    def add(self, line):
        self.table.append(line)
        return len(self.table) - 1  # return the index

    def get(self, index):
        return self.table[index]

    def size(self):
        return len(self.table)

    def display(self):
        print("\nMDT (Macro Definition Table)")
        print("-" * 40)
        for i, line in enumerate(self.table):
            print(f"{i:<5} {line}")
        print()


class ALA:
    """Argument List Array — maps formal parameters (@ARG) to actual
    arguments supplied in a macro call."""

    def __init__(self):
        # formal_param -> actual_arg
        self.table = {}

    def add(self, formal, actual):
        self.table[formal] = actual

    def get(self, formal):
        return self.table.get(formal, formal)

    def clear(self):
        self.table.clear()

    def substitute(self, line):
        """Replace every formal parameter in *line* with its actual value."""
        result = line
        for formal, actual in self.table.items():
            result = result.replace(formal, actual)
        return result

    def display(self):
        print("\nALA (Argument List Array)")
        print("-" * 40)
        for formal, actual in self.table.items():
            print(f"{formal:<15} -> {actual}")
        print()
