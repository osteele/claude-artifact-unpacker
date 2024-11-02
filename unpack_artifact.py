#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich",
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

console = Console()

def find_project_name(package_content):
    """Extract project name from package.json content or generate a default name."""
    try:
        # Very basic JSON parsing - for more robust handling, use json module
        for line in package_content.split('\n'):
            if '"name"' in line:
                name = line.split(':')[1].strip().strip('",')
                return name
    except:
        pass

    # If we can't find/parse a name, generate one
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

def create_project(files):
    """Create project directory and all files."""
    if not files:
        console.print("[red]No files to process!", style="bold")
        return

    # Get project name from first file if it's package.json
    if files[0][0] == 'package.json':
        project_name = find_project_name(files[0][1])
    else:
        project_name = find_project_name("")

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
    console = Console()  # Regular console for stdout
    error_console = Console(stderr=True)  # Error console for stderr

    console.print("[bold blue]🚀 Project Generator[/bold blue]")

    try:
        # Collect all files to process
        all_files = []

        if len(sys.argv) > 1:
            # Process each input file provided as argument
            for input_file in sys.argv[1:]:
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

        create_project(all_files)

    except KeyboardInterrupt:
        error_console.print("\n[red]⛔ Process interrupted by user[/red]")
        sys.exit(1)
    except Exception as e:
        error_console.print(f"\n[red]❌ Error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == '__main__':
    main()
