# MiniMacro — Error Handling Reference Guide

> Plain-English explanations of every error the macroprocessor can detect,
> with sample files you can run to see each one in action.

---

## Quick Overview

The macroprocessor has **two passes**:

- **Pass 1** — reads macro *definitions* and builds the tables (MNT, MDT, ALA)
- **Pass 2** — reads macro *calls* and expands them using those tables

Errors in **Pass 1** are caught early (before any expansion happens).  
Errors in **Pass 2** are caught during expansion.

---

## Error 1 — Missing MACROEND

| Detail | Info |
|---|---|
| **Pass** | Pass 1 |
| **Sample file** | `input/sample_program4.txt` |
| **Error message** | `[Pass 1 Error] Missing MACROEND in macro definition for 'INCR'.` |

### What does it mean?

Every macro definition must have a clear **closing tag** — `MACROEND` — that tells the processor *"the macro body ends here"*.

Think of it like writing an essay inside brackets `( ... )`. If you open a bracket and never close it, the reader is confused about where your essay ends. Same thing here — if you open a macro with `MINIMACRO` but forget to write `MACROEND`, the processor keeps reading line after line looking for the closing tag, and eventually runs out of file to read.

### What triggers it?

```
MINIMACRO
INCR @X
PULL_VAL @X
ADD_VAL =1
PUSH_VAL @X
           <- MACROEND is missing here!

BEGIN_CODE
INCR A
END_CODE
```

### How the processor catches it

During Pass 1, a **nesting counter** tracks open/close pairs.  
It increments on `MINIMACRO` and decrements on `MACROEND`.  
If it reaches the end of the file and the counter is still `> 0`,
the error is raised.

---

## Error 2 — Missing Macro Header After MINIMACRO

| Detail | Info |
|---|---|
| **Pass** | Pass 1 |
| **Sample file** | `input/sample_program5.txt` |
| **Error message** | `[Pass 1 Error] Missing macro header after MINIMACRO keyword.` |

### What does it mean?

`MINIMACRO` is a keyword that says *"I'm about to define a macro — the very next line will be its name and parameters."*

If `MINIMACRO` appears as the **very last line** of the file (or has nothing after it), the processor tries to read the next line for the macro's name — and finds nothing.

Think of it like raising your hand to speak in class, and then when everyone looks at you, you say nothing. The teacher (processor) was expecting you to give a name!

### What triggers it?

```
BEGIN_CODE
LOAD_VAL A
END_CODE

MINIMACRO
           <- File ends here. No macro name given!
```

### How the processor catches it

Right after seeing `MINIMACRO`, the processor immediately tries to read the **next line** for the header.  
If we have gone past the end of the file, the error fires.

---

## Error 3 — Undefined Macro

| Detail | Info |
|---|---|
| **Pass** | Pass 2 |
| **Sample file** | `input/sample_program6.txt` |
| **Error message** | `[Pass 2 Error] Undefined macro: 'DECR'` |

### What does it mean?

When the processor sees a word in all-caps with arguments in the code section (like `DECR B`), it checks its **Macro Name Table (MNT)** — basically a lookup dictionary of every macro that was defined.

If it can't find that word in the MNT, it means you're trying to **call a macro that was never written**. Like dialling a phone number that doesn't exist.

### What triggers it?

```
MINIMACRO
INCR @X          <- only INCR is defined
...
MACROEND

BEGIN_CODE
INCR A           <- fine, INCR exists
DECR B           <- ERROR! DECR was never defined
END_CODE
```

### How the processor catches it

During Pass 2, every all-caps opcode that has arguments is checked against `MNT.lookup()`.  
If the result is `None` and the opcode is not a known built-in directive,
the error is raised immediately.

---

## Error 4 — Wrong Number of Arguments

| Detail | Info |
|---|---|
| **Pass** | Pass 2 |
| **Sample file** | `input/sample_program7.txt` |
| **Error message** | `[Pass 2 Error] Incorrect number of arguments for macro 'SWAP': expected 2, got 1.` |

### What does it mean?

Every macro definition declares exactly how many inputs (parameters) it needs.  
When you *call* that macro, you must supply exactly that many arguments — no more, no less.

Think of a function like `SWAP(X, Y)`. If you call it as `SWAP(X)` with only one value, there's nothing to swap *to*. The processor refuses to guess.

### What triggers it?

```
MINIMACRO
SWAP @A,@B       <- SWAP needs 2 arguments
...
MACROEND

BEGIN_CODE
SWAP X,Y         <- fine, 2 arguments supplied
SWAP Z           <- ERROR! only 1 argument given, expected 2
END_CODE
```

### How the processor catches it

The MNT stores the **expected parameter count** for each macro.  
In Pass 2, before expanding, the processor compares:

```
len(actual_args)  vs  entry["param_count"]
```

If they don't match, the error fires.

---

## Error 5 — Maximum Recursion Depth (Infinite Loop)

| Detail | Info |
|---|---|
| **Pass** | Pass 2 |
| **Sample file** | `input/sample_program8.txt` |
| **Error message** | `[Pass 2 Error] Maximum macro expansion depth exceeded (possible infinite recursion).` |

### What does it mean?

A macro can call other macros inside its body — that's called **nested expansion**.  
But what if a macro calls *itself*? It would expand forever, like two mirrors facing each other.

To prevent this from crashing the program with an infinite loop, the processor has a **depth limit of 50 levels**. If expansion goes deeper than 50 levels, it assumes something is wrong and stops.

### What triggers it?

```
MINIMACRO
LOOP @N
PULL_VAL @N
LOOP @N          <- LOOP calls itself — infinite recursion!
MACROEND

BEGIN_CODE
LOOP A
END_CODE
```

When `LOOP A` is expanded:
- It sees `LOOP #1` inside → expands `LOOP A` again
- That sees `LOOP #1` → expands again
- ... forever, until depth > 50 → **error**

### How the processor catches it

The internal `_expand_macro` function takes a `depth` counter.  
Every recursive call increments it by 1.  
If `depth > 50`, the error is raised immediately.

---

## Summary Table

| # | Error Name | Pass | Trigger | Sample File |
|---|---|---|---|---|
| 1 | Missing `MACROEND` | Pass 1 | Macro body never closed | `sample_program4.txt` |
| 2 | Missing macro header | Pass 1 | `MINIMACRO` at end of file | `sample_program5.txt` |
| 3 | Undefined macro | Pass 2 | Calling a macro that was never defined | `sample_program6.txt` |
| 4 | Wrong argument count | Pass 2 | Too few or too many arguments in a call | `sample_program7.txt` |
| 5 | Max recursion depth | Pass 2 | Macro calls itself (directly or indirectly) | `sample_program8.txt` |

---

## How to Run Each Error Demo

```powershell
# From the project root (c:\Projects\spcc)
python main.py input/sample_program4.txt   # Error 1 — Missing MACROEND
python main.py input/sample_program5.txt   # Error 2 — Missing macro header
python main.py input/sample_program6.txt   # Error 3 — Undefined macro
python main.py input/sample_program7.txt   # Error 4 — Wrong argument count
python main.py input/sample_program8.txt   # Error 5 — Infinite recursion
```

> All errors print a clean `[Pass N Error] ...` message and exit gracefully —
> no crashes, no stack traces shown to the user.
