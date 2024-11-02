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

def process_input(input_stream):
    """Process the input stream and create files/directories."""
    current_file = None
    current_content = []
    files_to_process = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Processing input...", total=None)

        for line in input_stream:
            line = line.rstrip('\n')

            # Check for new file marker
            if line.startswith('// '):
                content = line[3:]  # Remove the '// ' prefix

                # If this is a placeholder for the previous file
                if content.startswith('[') and content.endswith(']'):
                    if current_file:
                        files_to_process.append((current_file, content))
                        current_file = None
                        current_content = []
                    continue

                # Save previous file if exists
                if current_file:
                    files_to_process.append((current_file, '\n'.join(current_content) if current_content else ''))
                    current_content = []

                current_file = content
                progress.update(task, description=f"[cyan]Found file: {current_file}")
                sleep(0.1)  # Add a small delay for visual effect

            elif current_file:
                current_content.append(line)

        # Don't forget the last file
        if current_file:
            files_to_process.append((current_file, '\n'.join(current_content) if current_content else ''))

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
        # Read from file if specified, otherwise from stdin
        if len(sys.argv) > 1:
            try:
                with open(sys.argv[1], 'r') as f:
                    files = process_input(f)
            except FileNotFoundError:
                error_console.print(f"\n[red]❌ Error: Input file not found: {sys.argv[1]}[/red]")
                sys.exit(1)
        else:
            console.print("[yellow]Reading from standard input (Ctrl+D to finish)...")
            files = process_input(sys.stdin)

        create_project(files)

    except KeyboardInterrupt:
        error_console.print("\n[red]⛔ Process interrupted by user[/red]")
        sys.exit(1)
    except Exception as e:
        error_console.print(f"\n[red]❌ Error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == '__main__':
    main()
