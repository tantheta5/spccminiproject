# MiniMacro — Two-Pass Macroprocessor

A simple educational macroprocessor written in Python 3 that demonstrates a **two-pass macro expansion** system. Built as a college mini-project for Systems Programming & Compiler Construction (SPCC).

---

## Criterion 1: Language Definition & Specification

MiniMacro is a custom, user-defined language designed specifically to demonstrate macro processing.

### Supported Keywords and Statements

| Keyword    | Purpose                        | Phase Handled In |
|------------|--------------------------------|------------------|
| `MINIMACRO`| Marks the start of a macro definition block. | Pass 1 |
| `MACROEND` | Marks the end of a macro definition block.   | Pass 1 |
| `BEGIN_CODE`| Indicates the beginning of the main executable program. | Pass 2 (Copied) |
| `END_CODE`  | Indicates the termination of the main executable program. | Pass 2 (Copied) |
| `PULL_VAL`  | Custom instruction: Pull a value from memory into a register. | Pass 2 (Copied/Expanded) |
| `ADD_VAL`   | Custom instruction: Add a value to a register. | Pass 2 (Copied/Expanded) |
| `PUSH_VAL`  | Custom instruction: Push a value from a register to memory. | Pass 2 (Copied/Expanded) |

### Syntax Rules and Delimiters

1. **Parameter Delimiter (`@`)**: Formal parameters within a macro definition must be prefixed with the `@` symbol (e.g., `@X`, `@Y`). This allows the processor to easily distinguish between formal parameters that need substitution and regular operands.
2. **Macro Definition Block**: A macro definition must strictly follow this structure:
   - Line 1: `MINIMACRO`
   - Line 2: Macro Header containing the macro name and space-separated formal parameters (e.g., `INCR @X`).
   - Line 3 to N: The macro body containing instructions.
   - Line N+1: `MACROEND`
3. **Macro Invocation**: A macro is called by stating its name followed by the actual arguments separated by spaces or commas (e.g., `INCR A`).

---

## Criterion 2: Design of Translation Phases

The processor is divided into two distinct logical phases to handle forward references and nested macros correctly.

### Pass 1: Analysis & Definition Processing
**Goal:** Scan the source code to identify all macro definitions, strip them from the main program, and build the necessary reference tables.

1. **Line-by-line Scanning:** Reads the source file sequentially.
2. **Detection:** When `MINIMACRO` is encountered, Pass 1 enters "definition mode".
3. **Table Population:**
   - It reads the next line (the header) to extract the macro name and parameter count.
   - It creates an entry in the **MNT (Macro Name Table)** containing: `Macro Name`, `Start Index in MDT`, and `# of Parameters`.
   - It copies the header and all subsequent lines into the **MDT (Macro Definition Table)** until it encounters `MACROEND`.
4. **Intermediate Output:** Any line not part of a `MINIMACRO`...`MACROEND` block is written to an intermediate data structure (a list in memory) representing the source code with definitions removed.

### Pass 2: Synthesis & Macro Expansion
**Goal:** Take the intermediate code from Pass 1, identify macro calls, and expand them into standard instructions using argument substitution.

1. **Sequential Reading:** Reads the intermediate code line by line.
2. **MNT Lookup:** For every line, it checks the first token (opcode) against the **MNT**.
   - If *not* found: The line is copied directly to the final output.
   - If *found*: It triggers the expansion routine.
3. **ALA Setup:** The **ALA (Argument List Array)** is cleared and populated by mapping the formal parameters found in the MDT header to the actual arguments provided in the current call.
4. **Expansion:** It iterates through the MDT starting from the macro's index + 1. For each line, it uses the ALA to substitute `@` parameters with actual arguments. The substituted lines are appended to the final output.
5. **Recursion:** If an expanded line is itself a macro call (found in MNT), Pass 2 recursively calls its expansion function.

---

## Criterion 3: Demonstration Using Sample Input

### Sample Input (`input/sample_program.txt`)
```
MINIMACRO
INCR @X
PULL_VAL @X
ADD_VAL =1
PUSH_VAL @X
MACROEND

BEGIN_CODE
INCR A
INCR B
END_CODE
```

### Step-by-Step Walkthrough

**--- PASS 1 ---**
1. **Line 1 (`MINIMACRO`)**: Detected. Pass 1 knows a definition is starting.
2. **Line 2 (`INCR @X`)**: Header parsed. `INCR` is added to **MNT** at MDT index 0 with 1 parameter. Line added to **MDT**.
3. **Line 3-5**: `PULL_VAL @X`, `ADD_VAL =1`, `PUSH_VAL @X` are sequentially appended to the **MDT**.
4. **Line 6 (`MACROEND`)**: Definition ends. Appended to **MDT**.
5. **Line 8-11**: `BEGIN_CODE`, `INCR A`, `INCR B`, `END_CODE` are outside any definition. They are saved as the **Intermediate Program**.

**--- PASS 2 ---**
1. **Line `BEGIN_CODE`**: Not in MNT. Copied to Final Output.
2. **Line `INCR A`**: `INCR` found in MNT! Expansion begins:
   - **ALA setup**: `@X` is mapped to `A`.
   - **MDT traversal**: 
     - MDT[1] `PULL_VAL @X` -> Substitute using ALA -> `PULL_VAL A` -> Added to Final Output.
     - MDT[2] `ADD_VAL =1` -> Substitute using ALA -> `ADD_VAL =1` -> Added to Final Output.
     - MDT[3] `PUSH_VAL @X` -> Substitute using ALA -> `PUSH_VAL A` -> Added to Final Output.
3. **Line `INCR B`**: `INCR` found in MNT. Expansion begins:
   - **ALA setup**: `@X` is mapped to `B`.
   - **MDT traversal**: Output becomes `PULL_VAL B`, `ADD_VAL =1`, `PUSH_VAL B`.
4. **Line `END_CODE`**: Not in MNT. Copied to Final Output.

---

## Criterion 4: Error Detection & Reporting

The system actively monitors for semantic and syntax errors during both passes to prevent malformed code generation.

| Error Condition | Example | Detection Mechanism | Error Message |
|-----------------|---------|---------------------|---------------|
| **Missing MACROEND** | A `MINIMACRO` block without a closing `MACROEND` | **Pass 1:** Tracks nesting level. If it reaches the end of the file while `nest_level > 0`, it raises a `RuntimeError`. | `Missing MACROEND in macro definition for 'X'.` |
| **Missing Header** | `MINIMACRO` followed immediately by EOF | **Pass 1:** Attempts to read `i + 1` after `MINIMACRO`. If it hits bounds, it fails. | `Missing macro header after MINIMACRO keyword.` |
| **Undefined Macro** | `CALL UNKNOWN` | **Pass 2:** Looks up opcode in MNT. If missing and no valid assembly mnemonic matches (assumed custom op), it halts expansion. | `Undefined macro: 'UNKNOWN'` |
| **Incorrect Arguments** | `INCR A, B` (expects 1) | **Pass 2:** Compares the length of `actual_args` parsed from the line to the `param_count` stored in the MNT for that macro. | `Incorrect number of arguments for macro 'INCR': expected 1, got 2.` |
| **Infinite Recursion** | Macro calls itself infinitely | **Pass 2:** Tracks recursion depth during nested expansion. Caps at depth 50 to prevent stack overflow. | `Maximum macro expansion depth exceeded.` |

---

## Criterion 5: Final Output / Results

### Final Expanded Program (`output/expanded_program.txt`)

```
  BEGIN_CODE
  PULL_VAL A
  ADD_VAL =1
  PUSH_VAL A
  PULL_VAL B
  ADD_VAL =1
  PUSH_VAL B
  END_CODE
```

*The tables generated during the process (MNT, MDT, ALA) are printed to the console during execution to verify the internal state.*

---

## Getting Started
### 2. Run the Program
```bash
python main.py input/sample_program.txt
```
