#!/usr/bin/env python3
"""
Test suite for Unity Git Hooks
Replaces BATS-based tests with Python-based tests that work on macOS and Windows
"""

import os
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class GitHooksTestCase(unittest.TestCase):
    """Base test case with setup and teardown for git repository"""
    
    def setUp(self):
        """Create a temporary git repository for testing"""
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp(prefix='unity-git-hooks-test-')
        self.repo_dir = os.path.join(self.test_dir, 'repo')
        os.makedirs(self.repo_dir)
        
        # Initialize git repository
        self._run_git(['init'])
        self._run_git(['config', 'user.email', 'test@ci'])
        self._run_git(['config', 'user.name', 'test'])
        
        # Create Assets directory
        self.assets_dir = os.path.join(self.repo_dir, 'Assets')
        os.makedirs(self.assets_dir)
        
        # Set up hook script path
        script_dir = Path(__file__).parent / 'scripts'
        self.pre_commit_hook = str(script_dir / 'pre-commit')
    
    def tearDown(self):
        """Clean up temporary directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _run_git(self, args, check=True, capture_output=False):
        """
        Run git command in the test repository
        
        On Windows with Scoop mingit, use PowerShell to invoke git
        """
        if platform.system() == 'Windows':
            # Check if git is available via Scoop mingit
            git_cmd = self._find_git_windows()
            cmd = [git_cmd] + args
        else:
            cmd = ['git'] + args
        
        result = subprocess.run(
            cmd,
            cwd=self.repo_dir,
            check=check,
            capture_output=capture_output,
            text=True
        )
        
        if capture_output:
            return result
        return result.returncode
    
    def _find_git_windows(self):
        """
        Find git executable on Windows
        Prioritize Scoop mingit installation
        """
        # Try Scoop mingit first
        scoop_git = os.path.expandvars(r'%USERPROFILE%\scoop\apps\mingit\current\cmd\git.exe')
        if os.path.exists(scoop_git):
            return scoop_git
        
        # Try Scoop shims directory
        scoop_shim = os.path.expandvars(r'%USERPROFILE%\scoop\shims\git.exe')
        if os.path.exists(scoop_shim):
            return scoop_shim
        
        # Fallback to system git
        return 'git'
    
    def _run_hook(self, hook_path, check=False):
        """
        Run a git hook script
        
        On Windows, we need to use bash or sh to run the hook
        On Unix systems, we can run it directly
        """
        if platform.system() == 'Windows':
            # Use Git Bash on Windows
            git_bash = self._find_git_bash_windows()
            if git_bash:
                cmd = [git_bash, hook_path]
            else:
                # Try with sh from Git installation
                cmd = ['sh', hook_path]
        else:
            # On Unix systems, run directly
            cmd = [hook_path]
        
        result = subprocess.run(
            cmd,
            cwd=self.repo_dir,
            capture_output=True,
            text=True
        )
        
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )
        
        return result
    
    def _find_git_bash_windows(self):
        """Find Git Bash executable on Windows"""
        # Try Scoop mingit installation
        scoop_bash = os.path.expandvars(r'%USERPROFILE%\scoop\apps\mingit\current\usr\bin\bash.exe')
        if os.path.exists(scoop_bash):
            return scoop_bash
        
        # Try standard Git for Windows installation
        git_bash = r'C:\Program Files\Git\bin\bash.exe'
        if os.path.exists(git_bash):
            return git_bash
        
        return None


class TestPreCommitHook(GitHooksTestCase):
    """Test cases for pre-commit hook"""
    
    def test_ensuring_meta_is_committed(self):
        """Test that missing .meta file causes pre-commit to fail"""
        # Create an asset file without .meta
        asset_file = os.path.join(self.assets_dir, 'assets')
        Path(asset_file).touch()
        self._run_git(['add', 'Assets/assets'])
        
        # Run pre-commit hook - should fail
        result = self._run_hook(self.pre_commit_hook)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Error: Missing meta file', result.stderr)
        
        # Now add the .meta file
        meta_file = os.path.join(self.assets_dir, 'assets.meta')
        Path(meta_file).touch()
        self._run_git(['add', 'Assets/assets.meta'])
        
        # Run pre-commit hook - should succeed
        result = self._run_hook(self.pre_commit_hook, check=True)
        self.assertEqual(result.returncode, 0)
    
    def test_ignoring_assets_file_starting_with_dot(self):
        """Test that asset files starting with dot are ignored"""
        # Create a hidden asset file (no .meta needed)
        hidden_file = os.path.join(self.assets_dir, '.assets')
        Path(hidden_file).touch()
        self._run_git(['add', '--force', 'Assets/.assets'])
        
        # Run pre-commit hook - should succeed
        result = self._run_hook(self.pre_commit_hook, check=True)
        self.assertEqual(result.returncode, 0)
    
    def test_renaming_directory(self):
        """Test that renaming a directory requires updating .meta files"""
        # Create directory with .gitkeep and .meta
        dir_path = os.path.join(self.assets_dir, 'dir')
        os.makedirs(dir_path)
        
        gitkeep_file = os.path.join(dir_path, '.gitkeep')
        Path(gitkeep_file).touch()
        
        meta_file = os.path.join(self.assets_dir, 'dir.meta')
        Path(meta_file).touch()
        
        self._run_git(['add', '--force', '--all'])
        self._run_git(['commit', '-n', '-m', 'add Assets/dir'])
        
        # Rename the directory
        new_dir_path = os.path.join(self.assets_dir, 'dir-new')
        shutil.move(dir_path, new_dir_path)
        self._run_git(['add', '--force', '--all'])
        
        # Run pre-commit hook - should fail because old .meta still exists
        result = self._run_hook(self.pre_commit_hook)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Error: Redudant meta file', result.stderr)


def run_tests():
    """Run all tests"""
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
