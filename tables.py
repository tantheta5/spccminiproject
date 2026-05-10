"""
tables.py — Data structures for the MiniMacro macroprocessor.

MNT  (Macro Name Table)     — macro name → (MDT start index, param count)
MDT  (Macro Definition Table) — sequential list of macro body lines with
                                positional notation (#1, #2, …) replacing
                                formal parameters.
ALA_DEF  (Argument List Array – Definition-time)
         — positional index (#N) → formal parameter (@X)
ALA_EXP  (Argument List Array – Expansion-time, combined)
         — one table accumulating every macro call's argument bindings,
           grouped by call label.
"""


class MNT:
    """Macro Name Table — stores each macro's name, MDT start index,
    and number of formal parameters."""

    def __init__(self):
        # name -> {"index": int, "param_count": int}
        self.table = {}
        self._order = []          # preserve insertion order for display

    def add(self, name, mdt_index, param_count):
        if name not in self.table:
            self._order.append(name)
        self.table[name] = {"index": mdt_index, "param_count": param_count}

    def lookup(self, name):
        return self.table.get(name)

    def display(self):
        print("\nMNT (Macro Name Table)")
        print("-" * 40)
        print(f"{'Macro Name':<15} {'MDT Pointer':<12} {'#Params'}")
        print("-" * 40)
        for name in self._order:
            info = self.table[name]
            # Display 1-based pointer (header is at internal idx,
            # body starts at internal idx+1 → display as idx+1+1 = idx+2)
            # But we show the pointer to the *header* entry in 1-based:
            display_ptr = info['index'] + 1
            print(f"{name:<15} {display_ptr:<12} {info['param_count']}")
        print()


class MDT:
    """Macro Definition Table — stores the body of every macro definition
    as a flat, sequentially-indexed list of instruction lines.

    Formal parameters (@X, @Y, …) are stored as positional tokens
    (#1, #2, …) so that Pass 2 can substitute actual arguments by index.
    """

    def __init__(self):
        self.table = []       # list of instruction strings (with #N notation)

    def add(self, line):
        self.table.append(line)
        return len(self.table) - 1   # return the index

    def get(self, index):
        return self.table[index]

    def size(self):
        return len(self.table)

    def display(self):
        print("\nMDT (Macro Definition Table)")
        print("-" * 40)
        print(f"{'MDT Index':<12} {'MDT Entry'}")
        print("-" * 40)
        for i, line in enumerate(self.table):
            # Display 1-based index to match textbook convention
            display_idx = i + 1
            print(f"{display_idx:<12} {line}")
        print()


class ALA_DEF:
    """Argument List Array — Definition Phase.

    Built during Pass 1 for each macro.  Maps positional placeholders
    (#1, #2, …) to the original formal parameter names (@X, @Y, …).
    """

    def __init__(self):
        # list of (position_str, formal_param) in insertion order
        self.entries = []

    def add(self, position, formal):
        """position: '#1', '#2', …   formal: '@X', '@Y', … """
        self.entries.append((position, formal))

    def clear(self):
        self.entries.clear()

    # Return a dict {formal -> position} for use in positional substitution
    def formal_to_pos(self):
        return {formal: pos for pos, formal in self.entries}

    def display(self):
        print("\nALA — Definition Phase (Formal Parameter Mapping)")
        print("-" * 40)
        print(f"{'Position':<12} {'Parameter'}")
        print("-" * 40)
        for pos, formal in self.entries:
            print(f"{pos:<12} {formal}")
        print()


class ALA_EXP:
    """Argument List Array — Expansion Phase (combined).

    Accumulates the argument bindings for *every* macro call encountered
    in Pass 2, grouped by call label so the textbook table is produced.

    Structure:
        calls — ordered list of (call_label, [(position, actual_arg), …])
    """

    def __init__(self):
        self.calls = []          # [(label, [(pos, arg), …]), …]

    def record_call(self, macro_name, actual_args):
        """Record one macro call expansion.

        macro_name   : e.g. 'INCR'
        actual_args  : list of actual arguments in call order
        """
        args_label = " ".join(actual_args)
        label = f"{macro_name} {args_label}".strip()
        bindings = [(f"#{i+1}", arg) for i, arg in enumerate(actual_args)]
        self.calls.append((label, bindings))

    def get_latest_bindings(self):
        """Return the bindings for the most recently recorded call."""
        if not self.calls:
            return {}
        _, bindings = self.calls[-1]
        return {pos: arg for pos, arg in bindings}

    def display(self):
        print("\nALA — Expansion Phase (All Macro Calls)")
        print("-" * 50)
        for label, bindings in self.calls:
            print(f"  Call: {label}")
            print(f"  {'Position':<12} {'Actual Argument'}")
            print(f"  {'-'*30}")
            for pos, arg in bindings:
                print(f"  {pos:<12} {arg}")
            print()


# ---------------------------------------------------------------------------
# Legacy shim so existing code that imports 'ALA' still works
# ---------------------------------------------------------------------------
class ALA(ALA_EXP):
    """Backward-compatible alias for ALA_EXP."""
    pass
