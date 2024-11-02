import os
import shutil
import subprocess
from pathlib import Path
import pytest

TEST_INPUTS_DIR = Path("tests/test_inputs")
TEST_OUTPUT_DIR = Path("tests/test_output")
SCRIPT_PATH = Path(__file__).parent.parent / "claude_project_unpacker.py"

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
    TEST_OUTPUT_DIR.mkdir(exist_ok)

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
    project_dir = TEST_OUTPUT_DIR / "basic-test"

    expected_files = {
        "package.json",
        "README.md",
        "src/index.js"
    }

    created_files = get_all_files(project_dir)
    assert created_files == expected_files


def test_nested_directories():
    input_file = TEST_INPUTS_DIR / "nested_dirs.txt"
    result = run_script(input_file)
    assert result.returncode == 0

    # Script creates "project" directory when no package.json
    project_dir = TEST_OUTPUT_DIR / "project"

    expected_files = {
        "deep/nested/structure/file1.txt",
        "deep/nested/other/file2.txt",
        "deep/nested/empty/.gitkeep"
    }

    created_files = get_all_files(project_dir)
    assert created_files == expected_files


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


def test_special_cases():
    input_file = TEST_INPUTS_DIR / "special_cases.txt"
    result = run_script(input_file)
    assert result.returncode == 0

    project_dir = TEST_OUTPUT_DIR / "project"

    expected_files = {
        ".gitignore",
        ".env",
        "src/spaces in path/test.js",
        "src/special#chars/test.txt"
    }

    created_files = get_all_files(project_dir)
    assert created_files == expected_files


def test_nonexistent_input():
    input_file = TEST_INPUTS_DIR / "nonexistent.txt"
    result = run_script(input_file)
    assert result.returncode == 1
    assert "Error" in result.stderr

def test_stdin_input(tmp_path):
    """Test reading from stdin"""
    input_file = TEST_INPUTS_DIR / "basic.txt"
    with open(input_file) as f:
        result = subprocess.run(
            [str(SCRIPT_PATH)],
            input=f.read(),
            capture_output=True,
            text=True
        )

    assert result.returncode == 0
    project_dir = TEST_OUTPUT_DIR / "basic-test"

    expected_files = {
        "package.json",
        "README.md",
        "src/index.js"
    }

    created_files = get_all_files(project_dir)
    assert created_files == expected_files
