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
        
        # Install git hooks so they run automatically
        self._install_hooks()
    
    def tearDown(self):
        """Clean up temporary directory"""
        if os.path.exists(self.test_dir):
            # On Windows, git may keep file handles open, so we need to handle errors
            def handle_remove_readonly(func, path, exc):
                """Error handler for Windows readonly files"""
                import stat
                if not os.access(path, os.W_OK):
                    # Make the file writable and try again
                    os.chmod(path, stat.S_IWUSR)
                    func(path)
                else:
                    raise
            
            shutil.rmtree(self.test_dir, onerror=handle_remove_readonly)
    
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
        return shutil.which('git') or 'git'
    
    def _install_hooks(self):
        """
        Install git hooks into the test repository
        Hooks will be run automatically by git
        
        Uses the installation method specified by INSTALL_HOOKS_METHOD environment variable.
        If not set, defaults to install-hooks.py.
        """
        install_method = os.environ.get('INSTALL_HOOKS_METHOD', 'install-hooks.py')
        
        # Get the scripts directory
        script_dir = Path(__file__).parent / 'scripts'
        
        # Create hooks directory if it doesn't exist
        hooks_dir = os.path.join(self.repo_dir, '.git', 'hooks')
        os.makedirs(hooks_dir, exist_ok=True)
        
        # On non-Windows, ensure hook scripts are executable in the git index
        if platform.system() != 'Windows':
            hooks = ['pre-commit', 'post-checkout', 'post-merge']
            for hook in hooks:
                hook_script = script_dir / hook
                if hook_script.exists():
                    # Check if the file is executable
                    if not os.access(hook_script, os.X_OK):
                        raise RuntimeError(f"Hook script {hook} is not executable in the git index. "
                                         f"Run: git update-index --chmod=+x scripts/{hook}")
        
        if install_method == 'install-hooks.sh':
            # Use the shell script to install hooks
            install_script = script_dir / 'install-hooks.sh'
            if platform.system() == 'Windows':
                # On Windows, we need bash to run the shell script
                # Try Git Bash first
                bash_paths = [
                    os.path.expandvars(r'%PROGRAMFILES%\Git\bin\bash.exe'),
                    os.path.expandvars(r'%PROGRAMFILES(X86)%\Git\bin\bash.exe'),
                    r'C:\Program Files\Git\bin\bash.exe',
                ]
                bash_cmd = None
                for bash_path in bash_paths:
                    if os.path.exists(bash_path):
                        bash_cmd = bash_path
                        break
                
                if not bash_cmd:
                    bash_cmd = shutil.which('bash')
                
                if bash_cmd:
                    subprocess.run(
                        [bash_cmd, str(install_script)],
                        cwd=self.repo_dir,
                        check=True
                    )
                else:
                    # Raise error if bash is not available on Windows
                    raise RuntimeError("Bash is required to run install-hooks.sh on Windows, but it was not found")
            else:
                subprocess.run(
                    [str(install_script)],
                    cwd=self.repo_dir,
                    check=True
                )
        
        elif install_method == 'install-hooks.py':
            # Use the Python script to install hooks
            install_script = script_dir / 'install-hooks.py'
            # The install-hooks.py script expects user input for the repo path
            # and a second input for the "Press any key to exit" prompt
            # Now that install-hooks.py detects its directory automatically,
            # we can run it from anywhere
            subprocess.run(
                [sys.executable, str(install_script)],
                input=self.repo_dir + '\n\n',  # First for repo path, second for exit prompt
                text=True,
                check=True,
                capture_output=True
            )
        
        else:
            # Unknown installation method
            raise ValueError(f"Unknown installation method: {install_method}. "
                           f"Expected 'install-hooks.py' or 'install-hooks.sh'")



class TestPreCommitHook(GitHooksTestCase):
    """Test cases for pre-commit hook"""
    
    def test_ensuring_meta_is_committed(self):
        """Test that missing .meta file causes pre-commit to fail"""
        # Create an asset file without .meta
        asset_file = os.path.join(self.assets_dir, 'assets')
        Path(asset_file).touch()
        self._run_git(['add', 'Assets/assets'])
        
        # Try to commit - pre-commit hook should fail automatically
        result = self._run_git(['commit', '-m', 'test commit'], check=False, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Error: Missing meta file', result.stderr)
        
        # Now add the .meta file
        meta_file = os.path.join(self.assets_dir, 'assets.meta')
        Path(meta_file).touch()
        self._run_git(['add', 'Assets/assets.meta'])
        
        # Try to commit again - should succeed
        result = self._run_git(['commit', '-m', 'test commit'], check=False, capture_output=True)
        self.assertEqual(result.returncode, 0)
    
    def test_ignoring_assets_file_starting_with_dot(self):
        """Test that asset files starting with dot are ignored"""
        # Create a hidden asset file (no .meta needed)
        hidden_file = os.path.join(self.assets_dir, '.assets')
        Path(hidden_file).touch()
        self._run_git(['add', '--force', 'Assets/.assets'])
        
        # Commit should succeed via pre-commit hook
        result = self._run_git(['commit', '-m', 'test commit'], check=False, capture_output=True)
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
        self._run_git(['commit', '-m', 'add Assets/dir'])
        
        # Rename the directory
        new_dir_path = os.path.join(self.assets_dir, 'dir-new')
        shutil.move(dir_path, new_dir_path)
        self._run_git(['add', '--force', '--all'])
        
        # Try to commit - pre-commit hook should fail because old .meta still exists
        result = self._run_git(['commit', '-m', 'rename dir'], check=False, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
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
