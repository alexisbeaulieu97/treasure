# utils/password.py
import sys
from getpass import getpass


def get_password(prompt_message: str = "Enter password") -> str:
    """Securely prompts the user for a password."""
    # Added a default prompt, allow customization
    password = getpass(f"{prompt_message}: ")
    if not password:
        # Handle empty password input if necessary, e.g., raise error or re-prompt
        # For now, allowing empty password, though maybe not advisable.
        print("Warning: Empty password entered.", file=sys.stderr)
    return password
