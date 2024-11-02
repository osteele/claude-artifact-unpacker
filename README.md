# Claude Artifact Unpacker 🚀

A Python script designed to unpack and organize multi-file projects from
Claude's Artifacts feature. When Claude generates multiple files in a single
Artifact (like a complete project structure), this tool helps you extract and
create those files locally with the correct directory structure.

## Why This Tool? 🤔

When working with [Claude's Artifacts
feature](https://www.anthropic.com/news/artifacts), you might receive multiple
files in a single output - for example, a complete React project with
package.json, component files, and configuration. This tool makes it easy to
take that output and create a working local project structure.

### Common Scenarios 📋

**Scenario 1: Unpacking a Generated Project**
Claude gives you a complete project structure in an Artifact:
```text
// package.json
{
  "name": "my-react-app",
  "version": "1.0.0"
}

// src/App.jsx
function App() {
  return <div>Hello World</div>;
}
```

Run this tool, and it automatically creates the files in their correct locations:
```text
my-react-app/
├── package.json
└── src/
    └── App.jsx
```

## Features ✨

- 📁 Creates nested directory structures automatically
- 📝 Handles multiple files and their contents in a single input
- 🎯 Extracts project name from package.json or generates sensible defaults
- 🔄 Reads from files or standard input
- 🎨 Beautiful visual feedback with progress indicators and tree views
- ⚠️ Handles placeholder content with helpful reminders

## Installation

1. Ensure you have Python 3.6+ installed
2. [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
3. Download the script and make it executable:
   ```bash
   chmod +x unpack_artifact.py
   ```

## Usage

### Basic Usage

```bash
# From a file:
./unpack_artifact.py input_file.txt

# From standard input:
cat input_file.txt | ./unpack_artifact.py
# or
./unpack_artifact.py < input_file.txt
```

### Input Format

The input format is simple and human-readable:

- Each file starts with `//` followed by a space and the file path
- File contents follow immediately after the path
- A blank line followed by a `//␣` indicates the end of the current file's
  content
- For placeholder content, use `// [Description of what goes here]`

Example input:
```text
// package.json
{
  "name": "my-awesome-project",
  "version": "1.0.0",
  "description": "An awesome project"
}

// src/main.js
import React from 'react';
console.log('Hello, world!');

// src/components/Button.jsx
function Button() {
  return <button>Click me</button>;
}

// src/components/Modal.jsx
// [Previous Modal component code goes here]
```

This will create:
```text
my-awesome-project/
├── package.json
├── src/
│   ├── main.js
│   └── components/
│       ├── Button.jsx
│       └── Modal.jsx
```

### Features in Detail

1. **Project Naming**
   - Uses the `name` field from package.json if available
   - Falls back to "project", "project 2", etc. if no name is found

2. **Directory Structure**
   - Automatically creates nested directories as needed
   - Handles both Unix and Windows-style paths

3. **Placeholder Content**
   - Recognizes placeholder markers like `// [Previous code goes here]`
   - Creates the file with the placeholder text
   - Prints a reminder to replace the placeholder content

4. **Visual Feedback**
   - Shows real-time progress with spinning indicators
   - Displays a tree view of the created project structure
   - Uses color-coding for different types of messages:
     - 🔵 Blue: Processing information
     - 🟢 Green: Success messages
     - 🟡 Yellow: Warnings and placeholders
     - 🔴 Red: Errors

## Examples

### Basic Project Structure
```text
// package.json
{
  "name": "my-app",
  "version": "1.0.0"
}

// README.md
# My Application
Welcome to my app!

// src/index.js
console.log('Hello, world!');
```

### React Project with Placeholder
```text
// package.json
{
  "name": "react-app",
  "version": "1.0.0"
}

// src/components/Header.jsx
export default function Header() {
  return <header>My App</header>;
}

// src/components/Footer.jsx
// [Copy the footer from the design system]
```

## Error Handling

The script handles several types of errors gracefully:
- Invalid input format
- File system permissions issues
- Keyboard interrupts (Ctrl+C)
- Missing or malformed package.json

## Contributing

Feel free to open issues or submit pull requests with improvements. Some areas that could be enhanced:
- Additional input formats
- More customizable visual feedback
- Template support
- Configuration options

## License

This project is MIT licensed. Feel free to use it as you wish!

---

Made with ❤️ using Python 🐍 and [rich](https://github.com/Textualize/rich) 🌈

Written with [Claude](https://www.anthropic.com/claude) 🤖 and [Cursor](https://www.cursor.com) ✨
