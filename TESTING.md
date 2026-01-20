# Testing Unity Git Hooks

This document describes how to run tests for the Unity Git Hooks project.

## Overview

Tests are written in Python and can run on Linux, macOS, and Windows.

## Prerequisites

- Python 3.x
- Git

### Windows-specific

On Windows, the tests are designed to work with git installed via Scoop's mingit package:

```powershell
# Install Scoop (if not already installed)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
Invoke-RestMethod get.scoop.sh | Invoke-Expression

# Install mingit
scoop install mingit
```

Alternatively, the tests will work with any git installation (Git for Windows, etc.).

## Running Tests

### Linux and macOS

```bash
python3 test_hooks.py
```

or

```bash
./test_hooks.py
```

### Windows

```powershell
python test_hooks.py
```

## Test Structure

The test suite (`test_hooks.py`) includes:

- **TestPreCommitHook**: Tests for the pre-commit hook
  - `test_ensuring_meta_is_committed`: Verifies that .meta files must be committed with their assets
  - `test_ignoring_assets_file_starting_with_dot`: Verifies that hidden files (starting with `.`) don't require .meta files
  - `test_renaming_directory`: Verifies that renaming directories properly handles .meta files

## Continuous Integration

The project uses GitHub Actions to run tests on multiple platforms:

- Ubuntu (Linux)
- macOS
- Windows (with Scoop mingit)

See `.github/workflows/test-hooks.yml` for the CI configuration.

## Migrating from BATS

Previous tests were written using BATS (Bash Automated Testing System) in `tests.bat`. These have been replaced with Python-based tests for better cross-platform compatibility.

The old BATS workflow can be found in `.github/workflows/bats.yml`.
