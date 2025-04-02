# utils/data.py
from pathlib import Path
from typing import NamedTuple, Optional


def to_bytes(s):
    """Converts input to bytes if it's not already."""
    # Simplified handling
    if isinstance(s, bytes):
        return s
    if isinstance(s, str):
        return s.encode()
    # Consider raising TypeError for unsupported types
    raise TypeError(f"Cannot convert type {type(s)} to bytes")


def get_files(
    basepath_str: str, pattern: str, excludes_pattern: Optional[str] = None
) -> list[Path]:
    """Recursively finds files matching pattern, excluding excludes_pattern."""
    basepath = Path(basepath_str)
    files = []
    if not basepath.exists():
        # Let the caller handle non-existent paths if needed, or raise here
        return []  # Return empty list if base path doesn't exist

    if basepath.is_dir():
        includes = basepath.rglob(pattern)
        excludes = set(basepath.rglob(excludes_pattern)) if excludes_pattern else set()
        files.extend(
            [item for item in includes if item.is_file() and item not in excludes]
        )
    elif basepath.is_file():
        # If basepath itself is a file, check if it matches the pattern
        # This might need refinement based on exact desired behavior for single files
        if basepath.match(pattern):
            # Check against excludes if provided
            is_excluded = False
            if excludes_pattern:
                # Check if the single file matches the exclude pattern relative to *some* base
                # This part is tricky. Let's assume excludes only apply within directories.
                # Or, require excludes to be patterns like '*.tmp' not paths.
                # For simplicity now, single files passed directly are not excluded by pattern.
                pass  # Simple approach: don't apply excludes pattern to single file input

            # Check if the file itself matches the exclude pattern directly
            if excludes_pattern and basepath.match(excludes_pattern):
                is_excluded = True

            if not is_excluded:
                files.append(basepath)
    return files


# Define a simple structure to hold input data and its source
class InputData(NamedTuple):
    content: bytes
    source_path: Optional[Path]  # Path if from file, None if from stdin
