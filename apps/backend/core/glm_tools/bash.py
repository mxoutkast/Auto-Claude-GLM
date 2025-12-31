"""
Bash Tool for GLM Agent
========================

Executes bash commands with security validation.

Uses the existing security system from apps/backend/security/ to validate
commands against allowlists before execution.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


async def execute_bash(
    args: dict[str, Any],
    cwd: Path | None = None,
    security_profile: Any | None = None
) -> dict:
    """
    Execute a bash command with security validation.
    
    Args:
        args: {"command": str, "timeout": int (optional, default 300)}
        cwd: Working directory
        security_profile: Security profile for validation (from security/)
    
    Returns:
        {
            "stdout": str,
            "stderr": str,
            "exit_code": int,
            "command": str
        } or {"error": str}
    """
    try:
        command = args.get("command")
        timeout = args.get("timeout", 300)  # 5 minute default
        
        if not command:
            return {"error": "Missing required parameter: command"}
        
        if cwd is None:
            cwd = Path.cwd()
        
        # Validate command using security system
        if security_profile:
            is_allowed, reason = validate_command_with_profile(command, security_profile)
            if not is_allowed:
                logger.warning(f"Command blocked: {command[:100]}")
                return {
                    "error": f"Command blocked by security policy: {reason}",
                    "command": command,
                    "blocked": True
                }
        else:
            logger.warning("No security profile provided - command validation skipped")
        
        # Execute command
        logger.info(f"Executing: {command[:100]}...")
        
        # On Windows, translate common Unix commands to Windows equivalents
        if os.name == 'nt':
            import re
            # Simple translations for common commands
            command = re.sub(r'^ls\s+-la\b', 'dir', command)
            command = re.sub(r'^ls\s+-l\b', 'dir', command)
            command = re.sub(r'^ls\b', 'dir', command)
            command = re.sub(r'\bgrep\b', 'findstr', command)
            command = re.sub(r'\bcat\b', 'type', command)
        
        try:
            # Run command with timeout
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd.resolve()),
                env=os.environ.copy()
            )
            
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "error": f"Command timed out after {timeout} seconds",
                    "command": command,
                    "timeout": True
                }
            
            stdout = stdout_bytes.decode('utf-8', errors='replace')
            stderr = stderr_bytes.decode('utf-8', errors='replace')
            exit_code = process.returncode
            
            logger.info(f"Command completed with exit code: {exit_code}")
            
            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "command": command,
                "success": exit_code == 0
            }
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "error": f"Execution error: {str(e)}",
                "command": command
            }
        
    except Exception as e:
        logger.error(f"Bash tool failed: {e}")
        return {"error": str(e)}


def validate_command_with_profile(command: str, security_profile: Any) -> tuple[bool, str]:
    """
    Validate command against security profile.
    
    Args:
        command: Full command line to validate
        security_profile: SecurityProfile instance from security/
    
    Returns:
        (is_allowed: bool, reason: str)
    """
    try:
        # Import security validation from existing system
        from security import is_command_allowed
        from security.parser import extract_commands
        
        # Extract base command names from the full command line
        # e.g., "git status" -> ["git"]
        commands = extract_commands(command)
        
        if not commands:
            return False, "No valid commands found"
        
        # Validate each command
        for cmd in commands:
            is_allowed, reason = is_command_allowed(cmd, security_profile)
            if not is_allowed:
                return False, reason
        
        return True, ""
        
    except ImportError:
        logger.warning("Security module not available - allowing command")
        return True, "Security validation unavailable"
    except Exception as e:
        logger.error(f"Security validation error: {e}")
        return False, f"Validation error: {str(e)}"
