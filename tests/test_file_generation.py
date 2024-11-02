import os
import shutil
import subprocess
from pathlib import Path
import pytest
from io import StringIO

import sys
sys.path.append(str(Path(__file__).parent.parent))
from unpack_artifact import process_input, find_project_name

SCRIPT_PATH = Path(__file__).parent.parent / "unpack_artifact.py"

TEST_INPUTS_DIR = Path("tests/test_inputs")
TEST_OUTPUT_DIR = Path("tests/test_output")

def setup_module():
    """Create output directory before tests"""
    TEST_OUTPUT_DIR.mkdir(exist_ok=True)
    # Ensure script is executable
    SCRIPT_PATH.chmod(0o755)

def teardown_module():
    """Clean up output directory after tests"""
    if TEST_OUTPUT_DIR.exists():
        shutil.rmtree(TEST_OUTPUT_DIR)

@pytest.fixture(autouse=True)
def clean_output_before_test():
    """Clean output directory before each test"""
    if TEST_OUTPUT_DIR.exists():
        shutil.rmtree(TEST_OUTPUT_DIR)
    TEST_OUTPUT_DIR.mkdir()

def get_all_files(directory):
    """Helper function to get all files in directory recursively"""
    return set(
        str(p.relative_to(directory))
        for p in Path(directory).rglob("*")
        if p.is_file()
    )

def run_script(input_file):
    """Run the script with the given input file"""
    # Convert script path to absolute before changing directories
    script_absolute = SCRIPT_PATH.resolve()
    input_absolute = input_file.resolve()

    # Save current working directory
    original_cwd = os.getcwd()

    try:
        # Change to test output directory
        os.chdir(TEST_OUTPUT_DIR)

        # Run script using absolute paths
        result = subprocess.run(
            [str(script_absolute), str(input_absolute)],
            capture_output=True,
            text=True
        )
        return result
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

def test_basic_generation():
    input_file = TEST_INPUTS_DIR / "basic.txt"
    result = run_script(input_file)
    assert result.returncode == 0

    # Script creates directory based on package.json name
    project_dir = TEST_OUTPUT_DIR /"basic-test"

    expected_files = {
        "package.json",
        "README.md",
        "src/index.js"
    }

    created_files = get_all_files(project_dir)
    assert created_files == expected_files

    # Cleanup
    shutil.rmtree(project_dir)

def test_nested_directories():
    input_file = TEST_INPUTS_DIR / "nested_dirs.txt"
    result = run_script(input_file)
    assert result.returncode == 0

    # Script creates "project" directory when no package.json
    project_dir = TEST_OUTPUT_DIR / "project"

    expected_files = {
        "deep/nested/structure/file1.txt",
        "deep/nested/other/file2.txt"
    }

    created_files = get_all_files(project_dir)
    assert created_files == expected_files

    # Cleanup
    shutil.rmtree(project_dir)

def test_placeholders():
    input_file = TEST_INPUTS_DIR / "placeholders.txt"
    result = run_script(input_file)
    assert result.returncode == 0

    project_dir = TEST_OUTPUT_DIR / "project"

    expected_files = {
        "src/components/Header.jsx",
        "src/components/Footer.jsx",
        "src/components/Sidebar.jsx",
        "src/data/config.json"
    }

    created_files = get_all_files(project_dir)
    assert created_files == expected_files

    # Verify placeholder content
    with open(project_dir / "src/components/Footer.jsx") as f:
        content = f.read().strip()
        assert content == "[Insert footer component here]"

    # Cleanup
    shutil.rmtree(project_dir)

def test_special_cases():
    input_file = TEST_INPUTS_DIR / "special_cases.txt"
    result = run_script(input_file)
    assert result.returncode == 0

    project_dir = TEST_OUTPUT_DIR / "project"

    expected_files = {
        ".gitignore",
        ".env",
        "src/spaces in path/test.js",
        "src/special#chars/test.txt",
        "empty/empty-file.txt"
    }

    created_files = get_all_files(project_dir)
    assert created_files == expected_files

    # Cleanup
    shutil.rmtree(project_dir)

def test_nonexistent_input():
    input_file = TEST_INPUTS_DIR / "nonexistent.txt"
    result = run_script(input_file)
    assert result.returncode == 1
    assert "Error" in result.stderr

def test_stdin_input(tmp_path):
    """Test reading from stdin"""
    input_file = TEST_INPUTS_DIR.resolve() / "basic.txt"  # Use absolute path

    # Save current working directory
    original_cwd = os.getcwd()

    try:
        # Create test output directory if it doesn't exist
        TEST_OUTPUT_DIR.mkdir(exist_ok=True)

        with open(input_file) as f:
            result = subprocess.run(
                [str(SCRIPT_PATH.resolve())],  # Use absolute path
                input=f.read(),
                capture_output=True,
                text=True,
                cwd=str(TEST_OUTPUT_DIR)  # Convert to string and use direct path
            )
    finally:
        os.chdir(original_cwd)

    assert result.returncode == 0
    project_dir = TEST_OUTPUT_DIR / "basic-test"

    expected_files = {
        "package.json",
        "README.md",
        "src/index.js"
    }

    created_files = get_all_files(project_dir)
    assert created_files == expected_files

    # Cleanup
    shutil.rmtree(project_dir)

def test_mixed_marker_styles():
    input_text = """// file1.txt
content1

# file2.txt
content2

// file3.txt
content3

# file4.txt
content4
"""
    files = process_input(StringIO(input_text))

    assert set(name for name, _ in files) == {"file1.txt", "file3.txt"}
    assert files[0] == ("file1.txt", "content1\n\n# file2.txt\ncontent2")
    assert files[1] == ("file3.txt", "content3\n\n# file4.txt\ncontent4")

    input_text = """# file1.txt
content1

// file2.txt
content2

# file3.txt
content3

// file4.txt
content4
"""
    files = process_input(StringIO(input_text))
    assert set(name for name, _ in files) == {"file1.txt", "file3.txt"}
    assert files[0] == ("file1.txt", "content1\n\n// file2.txt\ncontent2")
    assert files[1] == ("file3.txt", "content3\n\n// file4.txt\ncontent4")

def test_hash_style_markers():
    input_text = """# file1.txt
content1

# file2.txt
# [needs implementation]
"""
    files = process_input(StringIO(input_text))

    assert set(name for name, _ in files) == {"file1.txt", "file2.txt"}
    assert files[0] == ("file1.txt", "content1")
    assert files[1] == ("file2.txt", "[needs implementation]")

def test_markdown_content_not_treated_as_marker():
    input_text = """// README.md
# My Project Title
This is a markdown file with headers.
# Another Header
## Subheader

// src/index.js
console.log('hello');
"""
    files = process_input(StringIO(input_text))

    assert set(name for name, _ in files) == {"README.md", "src/index.js"}
    assert files[0] == ("README.md", "# My Project Title\nThis is a markdown file with headers.\n# Another Header\n## Subheader")
    assert files[1] == ("src/index.js", "console.log('hello');")

def test_project_name_from_various_configs():
    """Test project name extraction from different config files"""

    # Test Cargo.toml
    cargo_input = """[package]
name = "rust-project"
version = "0.1.0"
"""
    assert find_project_name(cargo_input, "Cargo.toml") == "rust-project"

    # Test pyproject.toml with poetry
    pyproject_input = """[tool.poetry]
name = "python-project"
version = "0.1.0"
"""
    assert find_project_name(pyproject_input, "pyproject.toml") == "python-project"

    # Test setup.py
    setup_input = """
from setuptools import setup

setup(
    name="python-setup-project",
    version="0.1.0",
)
"""
    assert find_project_name(setup_input, "setup.py") == "python-setup-project"

    # Test go.mod
    go_input = """module github.com/user/go-project
go 1.16
"""
    assert find_project_name(go_input, "go.mod") == "go-project"

def test_project_name_sanitization():
    """Test that project names are properly sanitized"""
    # Test with package.json
    input_with_spaces = '{"name": "my project name"}'
    assert find_project_name(input_with_spaces, "package.json") == "my-project-name"

    # Test with Cargo.toml
    cargo_with_invalid = """[package]
name = "rust@project!"
"""
    assert find_project_name(cargo_with_invalid, "Cargo.toml") == "rust-project"

def test_project_name_priority():
    """Test that config files are checked in the correct priority order"""
    files = [
        ("go.mod", "module github.com/user/go-project"),
        ("package.json", '{"name": "npm-project"}'),
        ("Cargo.toml", '[package]\nname = "rust-project"'),
    ]

    # First file in priority list should be used
    result = subprocess.run(
        [str(SCRIPT_PATH)],
        input="\n".join(f"// {path}\n{content}\n" for path, content in files),
        capture_output=True,
        text=True,
        cwd=str(TEST_OUTPUT_DIR)
    )

    assert result.returncode == 0
    assert os.path.exists(TEST_OUTPUT_DIR / "go-project")
