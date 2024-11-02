#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich",
#     "tomli",
# ]
# ///

import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich import print as rprint
from time import sleep
import re
import tomli
from configparser import ConfigParser
import argparse

console = Console()

def extract_name_from_cargo_toml(content: str) -> str | None:
    """Extract project name from Cargo.toml"""
    try:
        data = tomli.loads(content)
        if 'package' in data and 'name' in data['package']:
            return data['package']['name']
    except:
        # Fall back to simple parsing if tomli fails
        for line in content.split('\n'):
            if line.strip().startswith('name = '):
                # Extract value between quotes
                match = re.search(r'name\s*=\s*"([^"]+)"', line)
                if match:
                    return match.group(1)
    return None

def extract_name_from_pyproject(content: str) -> str | None:
    """Extract project name from pyproject.toml"""
    try:
        data = tomli.loads(content)
        # Check poetry section first
        if 'tool' in data and 'poetry' in data['tool']:
            return data['tool']['poetry'].get('name')
        # Check project section
        if 'project' in data:
            return data['project'].get('name')
    except:
        return None
    return None

def extract_name_from_setup_py(content: str) -> str | None:
    """Extract project name from setup.py"""
    # Look for name parameter in setup() call
    match = re.search(r'setup\s*\([^)]*name\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)
    return None

def extract_name_from_go_mod(content: str) -> str | None:
    """Extract project name from go.mod"""
    # First line should be module name
    first_line = content.split('\n')[0].strip()
    if first_line.startswith('module '):
        # Get last part of module path as project name
        module_path = first_line[7:].strip()
        return module_path.split('/')[-1]
    return None

def find_project_name(package_content: str, filepath: str = '') -> str:
    """Extract project name from various config files or generate default."""

    # Try to extract name based on file type
    name = None

    if filepath.endswith('package.json'):
        try:
            for line in package_content.split('\n'):
                if '"name"' in line:
                    name = line.split(':')[1].strip().strip('",')
                    break
        except:
            pass

    elif filepath.endswith('Cargo.toml'):
        name = extract_name_from_cargo_toml(package_content)

    elif filepath.endswith('pyproject.toml'):
        name = extract_name_from_pyproject(package_content)

    elif filepath.endswith('setup.py'):
        name = extract_name_from_setup_py(package_content)

    elif filepath.endswith('go.mod'):
        name = extract_name_from_go_mod(package_content)

    # If we found a name, sanitize it
    if name:
        # Remove invalid characters, replace with dashes
        name = re.sub(r'[^\w\-\.]', '-', name)
        # Remove leading/trailing dashes
        name = name.strip('-')
        return name if name else generate_default_name()

    return generate_default_name()

def generate_default_name() -> str:
    """Generate a default project name if none found."""
    base_name = "project"
    i = 1
    while os.path.exists(base_name):
        base_name = f"project {i}"
        i += 1
    return base_name

def is_file_marker(line: str) -> bool:
    """Check if a line is a file marker using either # or // syntax."""
    return (line.startswith('// ') or line.startswith('# ')) and not (
        line.startswith('// [') or line.startswith('# [')
    )

def is_placeholder_marker(line: str) -> bool:
    """Check if a line is a placeholder marker using either # or // syntax."""
    return (line.startswith('// [') and line.endswith(']')) or (
        line.startswith('# [') and line.endswith(']')
    )

def extract_filepath(line: str) -> str:
    """Extract filepath from a marker line, handling both # and // syntax."""
    if line.startswith('// '):
        return line[3:]  # Strip "// "
    elif line.startswith('# '):
        return line[2:]  # Strip "# "
    return line

def process_input(input_stream) -> list[tuple[str, str]]:
    """
    Process input stream and return list of (filepath, content) tuples.
    Handles special cases like placeholders and empty files.
    """
    current_file = None
    current_content = []
    files_to_process = []
    marker_style = None  # Track which marker style this file uses

    for line in input_stream:
        line = line.rstrip('\n')

        # Detect marker style from first file marker
        if marker_style is None and (line.startswith('// ') or line.startswith('# ')):
            marker_style = '// ' if line.startswith('// ') else '# '

        # Check if this is a new file marker (must be preceded by blank line if not first)
        is_new_file = (
            marker_style and
            line.startswith(marker_style) and
            not line.startswith(marker_style + '[') and
            (not current_file or not current_content or current_content[-1] == '')
        )

        if is_new_file:
            # Handle previous file if exists
            if current_file:
                files_to_process.append((current_file, '\n'.join(current_content[:-1] if current_content else [])))
                current_content = []

            # Get new filepath
            current_file = line[len(marker_style):]

        # Regular content line or placeholder
        elif current_file:
            if marker_style and line.startswith(marker_style + '[') and line.endswith(']'):
                # This is a placeholder for the current file
                files_to_process.append((current_file, line[len(marker_style):]))
                current_file = None
                current_content = []
            else:
                current_content.append(line)

    # Don't forget the last file
    if current_file:
        files_to_process.append((current_file, '\n'.join(current_content)))

    return files_to_process

def create_project(files, project_name=None):
    """Create project directory and all files."""
    if not files:
        console.print("[red]No files to process!", style="bold")
        return

    # Only look for config files if project_name wasn't specified
    if project_name is None:
        # Look for config files in priority order
        config_files = {
            'package.json': None,
            'Cargo.toml': None,
            'pyproject.toml': None,
            'setup.py': None,
            'go.mod': None
        }

        # Find first available config file
        for filepath, content in files:
            if filepath in config_files:
                config_files[filepath] = content
                break

        # Get project name from first found config file
        for filepath, content in config_files.items():
            if content is not None:
                project_name = find_project_name(content, filepath)
                break

        # Fall back to default if no config files found
        if project_name is None:
            project_name = generate_default_name()

    # Create a tree visualization
    tree = Tree(f"[bold green]📁 {project_name}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"[green]Creating project: {project_name}", total=len(files))

        # Create project directory
        os.makedirs(project_name, exist_ok=True)

        # Process each file
        current_branches = {}
        for filepath, content in files:
            progress.update(task, advance=1, description=f"[green]Creating: {filepath}")
            sleep(0.2)  # Add a small delay for visual effect

            full_path = os.path.join(project_name, filepath)
            directory = os.path.dirname(full_path)

            # Create necessary directories
            os.makedirs(directory, exist_ok=True)

            # Update tree visualization
            path_parts = filepath.split('/')
            current_tree = tree
            for i, part in enumerate(path_parts[:-1]):
                current_path = '/'.join(path_parts[:i+1])
                if current_path not in current_branches:
                    current_branches[current_path] = current_tree.add(f"[bold blue]📁 {part}")
                current_tree = current_branches[current_path]
            current_tree.add(f"[bold yellow]📄 {path_parts[-1]}")

            # Write the file
            with open(full_path, 'w') as f:
                f.write(content)

            # If content is a placeholder, notify user
            if content.startswith('[') and content.endswith(']'):
                rprint(f"[yellow]⚠️  Note: Please replace {content} in {full_path}")

    # Show the final tree structure
    console.print("\n[bold green]✨ Project created successfully![/bold green]")
    console.print(Panel.fit(tree, title="Project Structure", border_style="green"))

def main():
    console = Console()
    error_console = Console(stderr=True)

    # Add argument parsing
    parser = argparse.ArgumentParser(description='Project Generator')
    parser.add_argument('files', nargs='*', help='Input files to process')
    parser.add_argument('--name', help='Specify the project directory name')
    args = parser.parse_args()

    console.print("[bold blue]🚀 Project Generator[/bold blue]")

    try:
        all_files = []

        if args.files:
            # Process each input file provided as argument
            for input_file in args.files:
                try:
                    with open(input_file, 'r') as f:
                        console.print(f"[cyan]Processing input file: {input_file}")
                        files = process_input(f)
                        all_files.extend(files)
                except FileNotFoundError:
                    error_console.print(f"\n[red]❌ Error: Input file not found: {input_file}[/red]")
                    sys.exit(1)
        else:
            # No arguments - read from stdin
            console.print("[yellow]Reading from standard input (Ctrl+D to finish)...")
            files = process_input(sys.stdin)
            all_files.extend(files)

        if not all_files:
            error_console.print("\n[red]❌ Error: No files to process[/red]")
            sys.exit(1)

        create_project(all_files, project_name=args.name)

    except KeyboardInterrupt:
        error_console.print("\n[red]⛔ Process interrupted by user[/red]")
        sys.exit(1)
    except Exception as e:
        error_console.print(f"\n[red]❌ Error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == '__main__':
    main()
