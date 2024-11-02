# Claude Artifact Unpacker Specification

## 1. Input Format

### 1.1. File Definition Structure
Each file definition MUST consist of:
1. A file path line that:
   - MUST start with exactly `// ` (two forward slashes and a space)
   - MUST be followed by a relative file path
   - File paths MAY contain forward slashes to indicate directory structure
   - File paths MUST NOT contain backward slashes (even on Windows)
   - File paths MUST NOT start with a forward slash
   - File paths MUST NOT contain relative directory indicators (`.` or `..`)

2. Followed by exactly ONE of:
   a. Content lines where:
      - Lines MUST NOT start with `// `
      - Content MAY contain any valid text, including blank lines
      - Content MUST be terminated by either:
        * A blank line followed by another file path line
        * The end of the input
   b. A placeholder line that:
      - MUST start with `// [`
      - MUST end with `]`
      - MUST be used to indicate content to be added later
      - MUST trigger a warning to the user about needed replacement
   c. An empty line, which:
      - MUST result in creation of an empty file (zero bytes)
      - MUST be followed by either another file path line or end of input

### 1.2. Examples
```text
// path/to/file.txt
This is the content
of the file

// path/to/empty-file.txt

// placeholder-file.js
// [Code needs to be added here]

// another/file.js
console.log("Hello");
```

## 2. Project Naming

### 2.1. Name Resolution
1. If the first file is `package.json`:
   - Parse the file looking for a `"name":` field
   - The name MUST be extracted from the value, stripping quotes and whitespace
   - The name MUST be sanitized to be a valid directory name
   - If parsing fails, fall back to default naming

2. Default naming:
   - Start with `project`
   - If `project` exists, try `project 2`
   - Continue incrementing the number until an unused name is found
   - Numbers MUST be separated from "project" by exactly one space

### 2.2. Name Validation
- Project names MUST NOT contain characters invalid for file systems
- Project names MUST NOT be empty
- Project names MUST NOT be absolute paths
- Project names MUST NOT contain path separators

## 3. Directory Creation

### 3.1. Project Directory
- A root directory MUST be created with the resolved project name
- If the directory already exists:
  - For package.json-based names: error and exit
  - For default names: continue incrementing until an unused name is found

### 3.2. Subdirectories
- All intermediate directories in file paths MUST be created
- Directory creation MUST use appropriate permissions (0o755 on Unix-like systems)
- Directory paths MUST be normalized to the current platform
- Creation MUST be atomic (all or nothing) per file

## 4. File Generation

### 4.1. File Writing
- Files MUST be created with read/write permissions for the owner (0o644 on Unix-like systems)
- File content MUST be written exactly as provided, preserving whitespace
- Files MUST use platform-appropriate line endings
- Empty files MUST be created (zero bytes) if no content is provided

### 4.2. File Collision Handling
- If a file would overwrite an existing file:
  - The operation MUST fail
  - An error message MUST be displayed
  - The script MUST exit with a non-zero status

## 5. Visual Feedback

### 5.1. Progress Indicators
- A spinner MUST be shown during input processing
- File creation progress MUST be indicated
- Each major operation MUST update the progress display

### 5.2. Tree Visualization
- A tree view of the created structure MUST be shown on completion
- Directories MUST be visually distinct from files
- Tree MUST reflect the actual created structure
- Tree MUST use appropriate Unicode characters if supported

### 5.3. Messages
- Success messages MUST be shown in green
- Warnings (including placeholders) MUST be shown in yellow
- Errors MUST be shown in red
- Processing status MUST be shown in cyan

## 6. Error Handling

### 6.1. Input Errors
- Invalid file markers MUST be reported
- Malformed package.json MUST NOT crash the script
- Missing input MUST be reported clearly

### 6.2. File System Errors
- Permission denied MUST be reported with the specific path
- Disk full conditions MUST be handled gracefully
- Path too long errors MUST be reported clearly

### 6.3. Runtime Errors
- Keyboard interrupts (Ctrl+C) MUST be caught and handled gracefully
- Stack traces MUST NOT be shown to end users
- All errors MUST exit with appropriate non-zero status codes

## 7. Standard Input/Output

### 7.1. Input Sources
- Script MUST accept input from either:
  - A file specified as command-line argument
  - Standard input (stdin)
- Script MUST NOT prompt for input

### 7.2. Output Handling
- All status output MUST go to stderr
- Error messages MUST go to stderr
- Tree visualization MUST go to stdout
- Progress indicators MUST go to stderr
- Warning messages MUST go to stderr

## 8. Command Line Interface

### 8.1. Arguments
- Script MUST accept zero or one arguments
- With zero arguments: read from stdin
- With one argument: read from specified file
- With more arguments: error and exit

### 8.2. Exit Codes
- 0: Success
- 1: General error
- 2: Invalid input
- 3: File system error
- 4: Permission error

## 9. Compatibility

### 9.1. Python Version
- Script MUST run on Python 3.6 or later
- Script MUST NOT require non-standard library modules except `rich`
- Script MUST be compatible with CPython implementation

### 9.2. Platform Support
- Script MUST run on Unix-like systems (Linux, macOS)
- Script MUST run on Windows
- Script MUST handle path separators appropriately per platform
- Script MUST handle file permissions appropriately per platform

## 10. Performance

### 10.1. Resource Usage
- Script MUST NOT read entire input into memory at once
- Script MUST process input in a streaming fashion
- Script MUST release file handles promptly

### 10.2. Large Files
- Script MUST handle large input files efficiently
- Script MUST handle large numbers of files
- Script MUST handle deeply nested directories
