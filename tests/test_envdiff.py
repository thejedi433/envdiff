"""Tests for envdiff."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from envdiff import parse_env_file, compare_envs, format_output, main


@pytest.fixture
def tmp_env_files(tmp_path):
    """Create temporary .env files for testing."""
    file1 = tmp_path / ".env.dev"
    file2 = tmp_path / ".env.prod"
    
    file1.write_text("""# Database config
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp_dev
DB_USER=admin
DB_PASS=secret123

# API keys
API_KEY=dev-key-123
REDIS_URL=redis://localhost:6379
DEBUG=true
""")
    
    file2.write_text("""# Database config
DB_HOST=prod-db.example.com
DB_PORT=5432
DB_NAME=myapp_prod
DB_USER=prod_user
DB_PASS=supersecret

# API keys
API_KEY=prod-key-xyz
NEW_RELIC_KEY=newrelic-123
DEBUG=false
""")
    
    return file1, file2


def test_parse_env_file_basic(tmp_path):
    """Test parsing basic .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text("KEY1=value1\nKEY2=value2\n")
    
    result = parse_env_file(env_file)
    
    assert result == {"KEY1": "value1", "KEY2": "value2"}


def test_parse_env_file_with_comments(tmp_path):
    """Test that comments are ignored."""
    env_file = tmp_path / ".env"
    env_file.write_text("# This is a comment\nKEY1=value1\n# Another comment\nKEY2=value2\n")
    
    result = parse_env_file(env_file)
    
    assert result == {"KEY1": "value1", "KEY2": "value2"}


def test_parse_env_file_with_empty_lines(tmp_path):
    """Test that empty lines are ignored."""
    env_file = tmp_path / ".env"
    env_file.write_text("KEY1=value1\n\n\nKEY2=value2\n")
    
    result = parse_env_file(env_file)
    
    assert result == {"KEY1": "value1", "KEY2": "value2"}


def test_parse_env_file_with_quotes(tmp_path):
    """Test that quoted values are unquoted."""
    env_file = tmp_path / ".env"
    env_file.write_text('KEY1="quoted value"\nKEY2=\'single quoted\'\nKEY3=no quotes\n')
    
    result = parse_env_file(env_file)
    
    assert result == {
        "KEY1": "quoted value",
        "KEY2": "single quoted",
        "KEY3": "no quotes"
    }


def test_parse_env_file_with_empty_values(tmp_path):
    """Test keys with empty values."""
    env_file = tmp_path / ".env"
    env_file.write_text("KEY1=\nKEY2=value2\n")
    
    result = parse_env_file(env_file)
    
    assert result == {"KEY1": "", "KEY2": "value2"}


def test_parse_env_file_nonexistent(tmp_path):
    """Test parsing nonexistent file returns empty dict."""
    nonexistent = tmp_path / ".env.nonexistent"
    
    result = parse_env_file(nonexistent)
    
    assert result == {}


def test_parse_env_file_with_spaces(tmp_path):
    """Test that whitespace around = is handled."""
    env_file = tmp_path / ".env"
    env_file.write_text("KEY1 = value1\nKEY2=value2 \n  KEY3  =  value3  \n")
    
    result = parse_env_file(env_file)
    
    assert result == {"KEY1": "value1", "KEY2": "value2", "KEY3": "value3"}


def test_compare_envs_identical(tmp_path):
    """Test comparing identical files."""
    file1 = tmp_path / ".env1"
    file2 = tmp_path / ".env2"
    content = "KEY1=value1\nKEY2=value2\n"
    
    file1.write_text(content)
    file2.write_text(content)
    
    diff, only1, only2 = compare_envs(file1, file2)
    
    assert diff == {}
    assert only1 == {}
    assert only2 == {}


def test_compare_envs_different_values(tmp_path):
    """Test comparing files with different values."""
    file1 = tmp_path / ".env1"
    file2 = tmp_path / ".env2"
    
    file1.write_text("KEY1=value1\nKEY2=common\n")
    file2.write_text("KEY1=different\nKEY2=common\n")
    
    diff, only1, only2 = compare_envs(file1, file2)
    
    assert diff == {"KEY1": ("value1", "different")}
    assert only1 == {}
    assert only2 == {}


def test_compare_envs_missing_keys(tmp_path):
    """Test comparing files with missing keys."""
    file1 = tmp_path / ".env1"
    file2 = tmp_path / ".env2"
    
    file1.write_text("KEY1=value1\nKEY2=value2\n")
    file2.write_text("KEY2=value2\nKEY3=value3\n")
    
    diff, only1, only2 = compare_envs(file1, file2)
    
    assert diff == {}
    assert only1 == {"KEY1": "value1"}
    assert only2 == {"KEY3": "value3"}


def test_compare_envs_complex(tmp_path):
    """Test complex comparison scenario."""
    file1 = tmp_path / ".env1"
    file2 = tmp_path / ".env2"
    
    file1.write_text("KEY1=value1\nKEY2=common\nKEY3=only1\n")
    file2.write_text("KEY1=different\nKEY2=common\nKEY4=only2\n")
    
    diff, only1, only2 = compare_envs(file1, file2)
    
    assert diff == {"KEY1": ("value1", "different")}
    assert only1 == {"KEY3": "only1"}
    assert only2 == {"KEY4": "only2"}


def test_format_output_identical():
    """Test formatting identical files."""
    output = format_output({}, {}, {}, "file1", "file2")
    
    assert "identical" in output


def test_format_output_with_diff():
    """Test formatting with differences."""
    diff = {"KEY1": ("val1", "val2")}
    only1 = {"KEY2": "value2"}
    only2 = {"KEY3": "value3"}
    
    output = format_output(diff, only1, only2, "file1", "file2")
    
    assert "Different values" in output
    assert "KEY1" in output
    assert "val1" in output
    assert "val2" in output
    assert "Only in file1" in output
    assert "KEY2" in output
    assert "Only in file2" in output
    assert "KEY3" in output


def test_format_output_empty_values():
    """Test formatting with empty values."""
    diff = {"KEY1": ("", "value")}
    only1 = {}
    only2 = {}
    
    output = format_output(diff, only1, only2, "file1", "file2")
    
    assert "(empty)" in output


def test_main_success(capsys, tmp_env_files):
    """Test main with identical files."""
    file1, file2 = tmp_env_files
    
    # Make them identical
    file2.write_text(file1.read_text())
    
    # Should not raise SystemExit when identical (exits with 0)
    sys.argv = ['envdiff', str(file1), str(file2)]
    main()
    
    captured = capsys.readouterr()
    assert "identical" in captured.out


def test_main_with_differences(capsys, tmp_env_files):
    """Test main with different files."""
    file1, file2 = tmp_env_files
    
    with pytest.raises(SystemExit) as exc_info:
        sys.argv = ['envdiff', str(file1), str(file2)]
        main()
    
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Different values" in captured.out or "Only in" in captured.out


def test_main_nonexistent_file(capsys, tmp_path):
    """Test main with nonexistent file."""
    file1 = tmp_path / ".env1"
    file1.write_text("KEY=value\n")
    nonexistent = tmp_path / ".env.nonexistent"
    
    with pytest.raises(SystemExit) as exc_info:
        sys.argv = ['envdiff', str(file1), str(nonexistent)]
        main()
    
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_main_missing_args():
    """Test main with missing arguments."""
    with pytest.raises(SystemExit) as exc_info:
        sys.argv = ['envdiff']
        main()
    
    assert exc_info.value.code == 2  # argparse error


def test_parse_env_file_with_equals_in_value(tmp_path):
    """Test handling values that contain = signs."""
    env_file = tmp_path / ".env"
    env_file.write_text("KEY1=value=with=equals\nKEY2=base64==\n")
    
    result = parse_env_file(env_file)
    
    assert result == {"KEY1": "value=with=equals", "KEY2": "base64=="}


def test_compare_envs_with_nonexistent_file(tmp_path):
    """Test comparing when one file doesn't exist."""
    file1 = tmp_path / ".env1"
    file1.write_text("KEY1=value1\n")
    nonexistent = tmp_path / ".env.nonexistent"
    
    diff, only1, only2 = compare_envs(file1, nonexistent)
    
    # All keys from file1 should be in only1
    assert only1 == {"KEY1": "value1"}
    assert only2 == {}
    assert diff == {}


def test_main_first_file_nonexistent(capsys, tmp_path):
    """Test main when the FIRST file doesn't exist (covers line 111-112)."""
    nonexistent = tmp_path / ".env.nonexistent"
    file2 = tmp_path / ".env2"
    file2.write_text("KEY=value\n")
    
    with pytest.raises(SystemExit) as exc_info:
        sys.argv = ['envdiff', str(nonexistent), str(file2)]
        main()
    
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err
    assert str(nonexistent.name) in captured.err or str(nonexistent) in captured.err


def test_module_as_script(tmp_path):
    """Test running module as python -m envdiff (covers __main__.py)."""
    file1 = tmp_path / ".env1"
    file2 = tmp_path / ".env2"
    file1.write_text("KEY=value\n")
    file2.write_text("KEY=different\n")
    
    result = subprocess.run(
        [sys.executable, '-m', 'envdiff', str(file1), str(file2)],
        capture_output=True, text=True
    )
    assert result.returncode == 1  # differences found
    assert "Different values" in result.stdout
