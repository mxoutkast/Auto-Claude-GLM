# Security Policy Fix: Python Import Support

## Problem Analysis

The security system was blocking Python commands that used the `-c` flag with inline code containing `import` statements. The error messages showed:

```json
{
  "error": "Command blocked by security policy: Command 'import' is not in the allowed commands for this project",
  "command": "python -c \"from gui_wrapper import IcoConverterGUI; import sys; sys.exit(0)\"",
  "blocked": true
}
```

### Root Cause

The command parser in `apps/backend/security/parser.py` was incorrectly parsing Python inline code as separate shell commands. When it encountered:

```bash
python -c "from gui_wrapper import IcoConverterGUI; import sys"
```

It was extracting `['python', 'import', 'sys']` as separate commands, treating Python keywords like `import` as shell commands.

## Solution Implemented

### Modified File: `apps/backend/security/parser.py`

Added special case handling for Python's `-c` flag (similar to existing PowerShell and cmd handling):

```python
# Special case for Python with -c flag: treat inline code as part of python command
if cmd_lower.startswith("python ") or cmd_lower.startswith("python3 ") or cmd_lower.startswith("python.exe "):
    tokens = command_string.strip().split()
    if len(tokens) >= 2 and tokens[1] == "-c":
        # Only validate 'python', not the inline code
        cmd_name = os.path.basename(tokens[0])
        return [cmd_name]
```

### How It Works

1. **Detection**: When a command starts with `python`, `python3`, or `python.exe`
2. **Flag Check**: Verifies the second token is `-c`
3. **Extraction**: Returns only the interpreter name (e.g., `['python']`)
4. **Result**: Python code inside the `-c` flag is not parsed as shell commands

### Verification

All test cases now pass:

✓ `python -c "from gui_wrapper import IcoConverterGUI; import sys; sys.exit(0)"` → `['python']`
✓ `python -c "print('Import successful')"` → `['python']`
✓ `python3 -c "import os; print(os.getcwd())"` → `['python3']`
✓ `python.exe -c "from pathlib import Path"` → `['python.exe']`
✓ `python script.py` → `['python']`
✓ `python -m module` → `['python']`

## Python Command Allowlist

Python is already included in the base allowed commands via:

- **Base Commands** (`apps/backend/project/command_registry/base.py`): Includes `node`, `npm`, `npx`, etc.
- **Language Commands** (`apps/backend/project/command_registry/languages.py`): Includes comprehensive Python tooling:
  - `python`, `python3`
  - `pip`, `pip3`, `pipx`
  - `ipython`, `jupyter`, `notebook`
  - `pdb`, `pudb` (debuggers)

## Impact

This fix allows:
- ✅ Python import testing: `python -c "from module import Class"`
- ✅ Quick Python scripts: `python -c "print('test')"`
- ✅ Python inline validation: `python -c "import sys; sys.exit(0)"`
- ✅ All Python interpreters: `python`, `python3`, `python.exe`

## Files Modified

1. **`apps/backend/security/parser.py`** - Added Python `-c` flag handling (lines 54-60)

## Testing

Run the test script to verify:
```bash
python test_parser_fix.py
```

All tests should pass with `✓ PASS` indicators.
