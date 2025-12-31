"""
Command Parsing Utilities
==========================

Functions for parsing and extracting commands from shell command strings.
Handles compound commands, pipes, subshells, and various shell constructs.
"""

import os
import re
import shlex


def split_command_segments(command_string: str) -> list[str]:
    """
    Split a compound command into individual command segments.

    Handles command chaining (&&, ||, ;) but not pipes (those are single commands).
    """
    # Split on && and || while preserving the ability to handle each segment
    segments = re.split(r"\s*(?:&&|\|\|)\s*", command_string)

    # Further split on semicolons
    result = []
    for segment in segments:
        sub_segments = re.split(r'(?<!["\'])\s*;\s*(?!["\'])', segment)
        for sub in sub_segments:
            sub = sub.strip()
            if sub:
                result.append(sub)

    return result


def extract_commands(command_string: str) -> list[str]:
    """
    Extract command names from a shell command string.

    Handles pipes, command chaining (&&, ||, ;), and subshells.
    Returns the base command names (without paths).
    
    Special handling for code/script flags (e.g., python -c, node -e):
    When a code flag is detected, the entire code argument is treated as a single unit
    and not parsed for additional commands.
    """
    commands = []

    # Special case: If the command is "powershell -Command ..." or "cmd /c ...",
    # only validate the interpreter, not the script inside
    cmd_lower = command_string.strip().lower()
    if (cmd_lower.startswith("powershell ") or cmd_lower.startswith("powershell.exe ") or
        cmd_lower.startswith("cmd ") or cmd_lower.startswith("cmd.exe ")):
        # Extract just the interpreter name
        first_token = command_string.strip().split()[0]
        cmd_name = os.path.basename(first_token)
        return [cmd_name]

    # Code/script flags that take a code argument as the next token
    # These should not have their arguments parsed for additional commands
    CODE_FLAGS = {
        '-c', '-e', '-E',  # Python, Perl, Ruby, etc.
        '--command', '--eval', '--execute',  # Long form variants
        '/c', '/k',  # Windows cmd.exe flags
    }

    # First, tokenize the entire command string using shlex to handle quotes properly
    try:
        tokens = shlex.split(command_string)
    except ValueError:
        # Malformed command (unclosed quotes, etc.)
        # Try simple whitespace split to at least get the first command
        simple_tokens = command_string.strip().split()
        if simple_tokens:
            cmd = os.path.basename(simple_tokens[0])
            if cmd and not cmd.startswith("-"):
                commands.append(cmd)
        return commands

    if not tokens:
        return commands

    # Now iterate through tokens and extract commands
    # We need to handle command chaining (&&, ||, ;, |) properly
    # while respecting that code arguments should not be split
    expect_command = True
    skip_next = False  # Skip the next token if it's a code argument

    for i, token in enumerate(tokens):
        # If we're skipping a code argument, continue
        if skip_next:
            skip_next = False
            continue

        # Shell operators indicate a new command follows
        if token in ("|", "||", "&&", "&", ";"):
            expect_command = True
            continue

        # Skip shell keywords that precede commands
        if token in (
            "if",
            "then",
            "else",
            "elif",
            "fi",
            "for",
            "while",
            "until",
            "do",
            "done",
            "case",
            "esac",
            "in",
            "!",
            "{",
            "}",
            "(",
            ")",
            "function",
        ):
            continue

        # Check if this is a code flag - if so, skip the next token
        if token.lower() in CODE_FLAGS:
            # Check if there's a next token to skip
            if i + 1 < len(tokens):
                skip_next = True
            continue

        # Skip flags/options (but not code flags, which we already handled)
        if token.startswith("-"):
            continue

        # Skip variable assignments (VAR=value)
        if "=" in token and not token.startswith("="):
            continue

        # Skip here-doc markers
        if token in ("<<", "<<<", ">>", ">", "<", "2>", "2>&1", "&>"):
            continue

        if expect_command:
            # Extract the base command name (handle paths like /usr/bin/python)
            cmd = os.path.basename(token)
            
            # Normalize Windows command variants (e.g., echo. -> echo)
            if cmd.endswith('.'):
                cmd = cmd[:-1]
            
            commands.append(cmd)
            expect_command = False

    return commands


def get_command_for_validation(cmd: str, segments: list[str]) -> str:
    """
    Find the specific command segment that contains the given command.
    """
    for segment in segments:
        segment_commands = extract_commands(segment)
        if cmd in segment_commands:
            return segment
    return ""
