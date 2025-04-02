#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from typing import Generator, Optional

# Adjust imports based on new structure
from utils.crypto import decrypt, encrypt
from utils.data import InputData, get_files
from utils.password import get_password

# --- Argument Parsing (mostly unchanged) ---
parser = argparse.ArgumentParser(
    description="Encrypt or decrypt files/stdin.",  # Added description
    formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=50),
)

parser.add_argument(
    "-k",
    "--keep",
    action="store_true",
    help="keep the original file when encrypting or decrypting from a file",
)
parser.add_argument(
    "-i",
    "--input",
    metavar="PATH",
    help="input file or directory path (reads from stdin if omitted)",
)
parser.add_argument(
    "-o",
    "--output",
    metavar="PATH",
    help="output file or directory path (writes to stdout if omitted)",
)

# Actions group
actions_group = parser.add_argument_group("action options")
actions_options = actions_group.add_mutually_exclusive_group(required=True)
actions_options.add_argument(
    "-l", "--lock", action="store_true", help="encrypt content"
)
actions_options.add_argument(
    "-u", "--unlock", action="store_true", help="decrypt content"
)

# --- Core Logic ---


def get_input_data(args: argparse.Namespace) -> Generator[InputData, None, None]:
    """Yields InputData objects from file(s) or stdin."""
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            raise FileNotFoundError(f"Input path not found: {args.input}")

        # Define patterns based on action
        # When unlocking, we expect .ENC files (adjust if suffix changes)
        pattern = "*.ENC" if args.unlock else "*"
        # Exclude .ENC files when locking to avoid re-encrypting
        excludes = "*.ENC" if args.lock else None

        files = get_files(args.input, pattern=pattern, excludes_pattern=excludes)
        if not files:
            print(
                f"Warning: No files matching pattern '{pattern}' (excluding '{excludes}') found in '{args.input}'.",
                file=sys.stderr,
            )
            return  # Stop generation if no files found

        for file_path in files:
            try:
                content = file_path.read_bytes()
                yield InputData(content=content, source_path=file_path)
            except IOError as e:
                print(f"Error reading file {file_path}: {e}", file=sys.stderr)
                # Decide whether to skip or exit. Skipping for now.
                continue
    else:
        # Read from stdin
        if sys.stdin.isatty():
            # Check if stdin is connected to a terminal and likely empty
            # Potentially wait for input, or exit if no pipe expected.
            # This check prevents hanging if run interactively without input redirection.
            print(
                "Reading from stdin. Use Ctrl+D (Unix) or Ctrl+Z+Enter (Windows) to end input.",
                file=sys.stderr,
            )

        stdin_data = sys.stdin.buffer.read()  # Read raw bytes
        if not stdin_data:
            raise ValueError("stdin received no data.")
        yield InputData(content=stdin_data, source_path=None)  # Source is stdin


def write_output_data(
    data: bytes, source_path: Optional[Path], args: argparse.Namespace
):
    """Writes data to the specified output file/directory or stdout."""
    output_path_str = args.output

    if output_path_str:
        output_path = Path(output_path_str)
        target_file_path: Path

        if output_path.is_dir():
            # Output is a directory, construct filename based on source
            if source_path is None:
                raise ValueError(
                    "Cannot write to output directory: input was from stdin."
                )

            base_filename = source_path.name
            if args.lock:
                target_filename = f"{base_filename}.ENC"
            elif args.unlock:
                # Attempt to remove .ENC suffix, handle cases without it
                target_filename = base_filename.removesuffix(".ENC")
                if target_filename == base_filename:
                    print(
                        f"Warning: Input file '{base_filename}' did not have .ENC suffix for unlocking.",
                        file=sys.stderr,
                    )
                    # Decide on behavior: append '.dec' or use original name? Using original for now.
            else:
                target_filename = (
                    base_filename  # Should not happen with mutually exclusive group
                )

            target_file_path = output_path / target_filename
        else:
            # Output is a specific file path
            target_file_path = output_path
            # Ensure parent directory exists if specifying a new file path
            target_file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            target_file_path.write_bytes(data)
            print(f"Output written to: {target_file_path}")  # Provide feedback
        except IOError as e:
            print(f"Error writing file {target_file_path}: {e}", file=sys.stderr)
            # Consider exiting or specific error handling

    else:
        # Write to stdout
        try:
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
        except IOError as e:
            print(f"Error writing to stdout: {e}", file=sys.stderr)


def delete_original_file(source_path: Optional[Path], args: argparse.Namespace):
    """Deletes the source file if conditions are met."""
    if source_path and args.input and not args.keep:
        try:
            source_path.unlink()
            print(f"Original file deleted: {source_path}")
        except OSError as e:
            print(f"Error deleting original file {source_path}: {e}", file=sys.stderr)


def run_lock(args: argparse.Namespace):
    """Encrypts data from input source(s)."""
    password = get_password("Enter password to encrypt")
    # Consider adding password confirmation here
    # password_confirm = get_password("Confirm password")
    # if password != password_confirm:
    #    print("Passwords do not match. Exiting.", file=sys.stderr)
    #    sys.exit(1)

    for input_data in get_input_data(args):
        try:
            encrypted_data = encrypt(input_data.content, password)
            write_output_data(encrypted_data, input_data.source_path, args)
            delete_original_file(input_data.source_path, args)
        except Exception as e:  # Catch potential errors during processing of one item
            source_name = input_data.source_path or "stdin"
            print(f"Error processing {source_name}: {e}", file=sys.stderr)
            # Decide: continue processing next item or exit? Continuing for now.


def run_unlock(args: argparse.Namespace):
    """Decrypts data from input source(s)."""
    # Get password once for all files in this run
    password = get_password("Enter password to decrypt")

    for input_data in get_input_data(args):
        try:
            decrypted_data = decrypt(input_data.content, password)
            write_output_data(decrypted_data, input_data.source_path, args)
            delete_original_file(input_data.source_path, args)
        except (
            ValueError
        ) as e:  # Catch specific decryption errors (wrong pass, corrupt)
            source_name = input_data.source_path or "stdin"
            print(f"Error decrypting {source_name}: {e}", file=sys.stderr)
            # Continue to next file, as password might be wrong only for this one
        except Exception as e:  # Catch other potential errors
            source_name = input_data.source_path or "stdin"
            print(f"Error processing {source_name}: {e}", file=sys.stderr)


# --- Main Execution ---
if __name__ == "__main__":
    args = parser.parse_args()

    try:
        # Select and run the action
        if args.lock:
            run_lock(args)
        elif args.unlock:
            run_unlock(args)
        else:
            # Should be unreachable due to required mutually exclusive group
            parser.error("No action specified.")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:  # Catch errors like empty stdin, decryption failure
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # Generic catch-all for unexpected errors
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

    # print("Operation completed.") # Optional success message
