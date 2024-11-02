#!/usr/bin/env python3

import sys
import os
from pathlib import Path

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

    for line in input_stream:
        line = line.rstrip('\n')

        # Check for new file marker
        if line.startswith('// '):
            # Save previous file if exists
            if current_file:
                files_to_process.append((current_file, '\n'.join(current_content)))
                current_content = []

            current_file = line[3:]  # Remove the '// ' prefix

            # Handle placeholder content marker
            if current_file.startswith('[') and current_content:
                # This is a placeholder marker for the previous file
                files_to_process.append((files_to_process.pop()[0], line[3:]))
                current_file = None
                continue

        elif current_file:
            current_content.append(line)

    # Don't forget the last file
    if current_file and current_content:
        files_to_process.append((current_file, '\n'.join(current_content)))

    return files_to_process

def create_project(files):
    """Create project directory and all files."""
    if not files:
        print("No files to process!")
        return

    # Get project name from first file if it's package.json
    if files[0][0] == 'package.json':
        project_name = find_project_name(files[0][1])
    else:
        project_name = find_project_name("")

    print(f"Creating project directory: {project_name}")
    os.makedirs(project_name, exist_ok=True)

    # Process each file
    for filepath, content in files:
        full_path = os.path.join(project_name, filepath)
        directory = os.path.dirname(full_path)

        # Create necessary directories
        os.makedirs(directory, exist_ok=True)

        # Write the file
        with open(full_path, 'w') as f:
            f.write(content)

        # If content is a placeholder, notify user
        if content.startswith('[') and content.endswith(']'):
            print(f"Note: Please replace {content} in {full_path}")
        else:
            print(f"Created: {full_path}")

def main():
    # Read from file if specified, otherwise from stdin
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            files = process_input(f)
    else:
        files = process_input(sys.stdin)

    create_project(files)

if __name__ == '__main__':
    main()
