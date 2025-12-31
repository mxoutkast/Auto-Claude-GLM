"""
Filesystem Tools for GLM Agent
===============================

Implements file system operations: Read, Write, Edit, Glob, Grep.

All tools validate paths are within the allowed working directory
and handle errors gracefully.
"""

import glob as glob_module
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def validate_path(file_path: str, cwd: Path | None = None) -> Path:
    """
    Validate file path is within allowed working directory.
    
    Args:
        file_path: File path (can be relative or absolute)
        cwd: Working directory (if None, current directory)
    
    Returns:
        Resolved Path object
    
    Raises:
        ValueError: If path escapes working directory
    """
    if cwd is None:
        cwd = Path.cwd()
    
    # Resolve path
    if Path(file_path).is_absolute():
        resolved = Path(file_path).resolve()
    else:
        resolved = (cwd / file_path).resolve()
    
    # Check if within cwd
    try:
        resolved.relative_to(cwd.resolve())
    except ValueError:
        raise ValueError(
            f"Path escapes working directory: {file_path}\n"
            f"Working directory: {cwd.resolve()}"
        )
    
    return resolved


async def execute_read(args: dict[str, Any], cwd: Path | None = None) -> dict:
    """
    Read contents of a file.
    
    Args:
        args: {"file_path": str}
        cwd: Working directory
    
    Returns:
        {"content": str} or {"error": str}
    """
    try:
        file_path = args.get("file_path")
        if not file_path:
            return {"error": "Missing required parameter: file_path"}
        
        path = validate_path(file_path, cwd)
        
        if not path.exists():
            return {"error": f"File not found: {file_path}"}
        
        if not path.is_file():
            return {"error": f"Not a file: {file_path}"}
        
        # Read with multiple encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        content = None
        
        for encoding in encodings:
            try:
                content = path.read_text(encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            return {"error": f"Unable to decode file: {file_path}"}
        
        logger.info(f"Read file: {path.relative_to(cwd) if cwd else path}")
        return {"content": content, "file_path": str(path)}
        
    except Exception as e:
        logger.error(f"Read failed: {e}")
        return {"error": str(e)}


async def execute_write(args: dict[str, Any], cwd: Path | None = None) -> dict:
    """
    Write content to a file.
    
    Args:
        args: {"file_path": str, "content": str}
        cwd: Working directory
    
    Returns:
        {"success": bool, "bytes_written": int} or {"error": str}
    """
    try:
        file_path = args.get("file_path")
        content = args.get("content")
        
        if not file_path:
            return {"error": "Missing required parameter: file_path"}
        if content is None:
            return {"error": "Missing required parameter: content"}
        
        path = validate_path(file_path, cwd)
        
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        path.write_text(content, encoding='utf-8')
        
        bytes_written = len(content.encode('utf-8'))
        logger.info(f"Wrote {bytes_written} bytes to: {path.relative_to(cwd) if cwd else path}")
        
        return {
            "success": True,
            "file_path": str(path),
            "bytes_written": bytes_written
        }
        
    except Exception as e:
        logger.error(f"Write failed: {e}")
        return {"error": str(e)}


async def execute_edit(args: dict[str, Any], cwd: Path | None = None) -> dict:
    """
    Edit a file by replacing old_string with new_string.
    
    Args:
        args: {
            "file_path": str,
            "old_string": str,
            "new_string": str
        }
        cwd: Working directory
    
    Returns:
        {"success": bool, "replacements": int} or {"error": str}
    """
    try:
        file_path = args.get("file_path")
        old_string = args.get("old_string")
        new_string = args.get("new_string")
        
        if not file_path:
            return {"error": "Missing required parameter: file_path"}
        if old_string is None:
            return {"error": "Missing required parameter: old_string"}
        if new_string is None:
            return {"error": "Missing required parameter: new_string"}
        
        path = validate_path(file_path, cwd)
        
        if not path.exists():
            return {"error": f"File not found: {file_path}"}
        
        # Read current content
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = path.read_text(encoding='latin-1')
        
        # Count occurrences
        count = content.count(old_string)
        if count == 0:
            return {
                "error": f"String not found in file: {old_string[:100]}...",
                "searched_file": str(path)
            }
        
        # Replace
        new_content = content.replace(old_string, new_string)
        
        # Write back
        path.write_text(new_content, encoding='utf-8')
        
        logger.info(
            f"Edited {path.relative_to(cwd) if cwd else path}: "
            f"{count} replacement(s)"
        )
        
        return {
            "success": True,
            "file_path": str(path),
            "replacements": count
        }
        
    except Exception as e:
        logger.error(f"Edit failed: {e}")
        return {"error": str(e)}


async def execute_glob(args: dict[str, Any], cwd: Path | None = None) -> dict:
    """
    Find files matching a glob pattern.
    
    Args:
        args: {"pattern": str}
        cwd: Working directory
    
    Returns:
        {"files": list[str]} or {"error": str}
    """
    try:
        pattern = args.get("pattern")
        if not pattern:
            return {"error": "Missing required parameter: pattern"}
        
        if cwd is None:
            cwd = Path.cwd()
        
        # Use glob to find matching files
        # Ensure pattern doesn't escape cwd
        if pattern.startswith('/') or pattern.startswith('..'):
            return {"error": "Pattern must not start with / or .."}
        
        matches = glob_module.glob(str(cwd / pattern), recursive=True)
        
        # Filter to only files within cwd
        filtered = []
        for match in matches:
            try:
                match_path = Path(match).resolve()
                match_path.relative_to(cwd.resolve())
                # Make relative to cwd for display
                rel_path = match_path.relative_to(cwd.resolve())
                filtered.append(str(rel_path))
            except ValueError:
                # Path outside cwd, skip
                continue
        
        logger.info(f"Glob pattern '{pattern}' matched {len(filtered)} files")
        
        return {
            "files": sorted(filtered),
            "count": len(filtered),
            "pattern": pattern
        }
        
    except Exception as e:
        logger.error(f"Glob failed: {e}")
        return {"error": str(e)}


async def execute_grep(args: dict[str, Any], cwd: Path | None = None) -> dict:
    """
    Search for pattern in files.
    
    Args:
        args: {
            "pattern": str (regex pattern),
            "file_pattern": str (glob pattern, optional),
            "case_sensitive": bool (default: True)
        }
        cwd: Working directory
    
    Returns:
        {"matches": list[dict]} or {"error": str}
    """
    try:
        pattern = args.get("pattern")
        file_pattern = args.get("file_pattern", "**/*.py")
        case_sensitive = args.get("case_sensitive", True)
        
        if not pattern:
            return {"error": "Missing required parameter: pattern"}
        
        if cwd is None:
            cwd = Path.cwd()
        
        # Compile regex
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return {"error": f"Invalid regex pattern: {e}"}
        
        # Get files to search
        glob_result = await execute_glob({"pattern": file_pattern}, cwd)
        if "error" in glob_result:
            return glob_result
        
        files = glob_result.get("files", [])
        
        # Search each file
        matches = []
        for file_path in files[:100]:  # Limit to 100 files
            try:
                full_path = cwd / file_path
                if not full_path.is_file():
                    continue
                
                content = full_path.read_text(encoding='utf-8', errors='ignore')
                
                # Find matches with line numbers
                for line_num, line in enumerate(content.splitlines(), 1):
                    if regex.search(line):
                        matches.append({
                            "file": str(file_path),
                            "line": line_num,
                            "content": line.strip()
                        })
                        
                        # Limit matches per file
                        if len([m for m in matches if m["file"] == str(file_path)]) >= 10:
                            break
                
            except Exception as e:
                logger.debug(f"Skipping {file_path}: {e}")
                continue
        
        logger.info(
            f"Grep pattern '{pattern}' found {len(matches)} matches "
            f"in {len(set(m['file'] for m in matches))} files"
        )
        
        return {
            "matches": matches[:100],  # Limit total matches
            "total_matches": len(matches),
            "pattern": pattern,
            "files_searched": len(files)
        }
        
    except Exception as e:
        logger.error(f"Grep failed: {e}")
        return {"error": str(e)}
