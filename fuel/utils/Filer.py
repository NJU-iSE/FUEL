"""
File management system for the FUEL project.
Provides file operations and path management functionality.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Optional


class _SimpleFileManager:
    """Internal file manager implementation."""

    def __init__(self, root_dir: str, res_dir: str, output_dir: str, lib: str):
        self.lib = lib
        self.root_dir = root_dir
        self.res_dir = os.path.join(root_dir, res_dir, lib)
        self.output_dir = os.path.join(root_dir, output_dir)
        self.test_dir = os.path.join(self.output_dir, lib)

        # Runtime state variables
        self.cur_filename = ""
        self.rendered_code = ""
        self.eliminated_code = ""

        # Initialize directories and file paths
        self._setup_directories()
        self._setup_file_paths()
        self._setup_library_path()

    def _setup_directories(self):
        """Set up directory structure."""
        # Create input directory
        if Path(self.res_dir).exists():
            shutil.rmtree(Path(self.res_dir))
        Path(self.res_dir).mkdir(parents=True)

        # Create output directory
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

        # Create test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
        os.makedirs(self.test_dir, exist_ok=True)

    def _setup_file_paths(self):
        """Set up file paths."""
        # Log files
        self.total_errs_file = os.path.join(self.test_dir, "total_errs.log")
        self.err_file = os.path.join(self.test_dir, "err.log")
        self.success_file = os.path.join(self.test_dir, "success.log")
        self.fail_file = os.path.join(self.test_dir, "fail.log")
        self.validate_file = os.path.join(self.test_dir, "validate.log")
        self.bug_file = os.path.join(self.test_dir, "bug.log")
        self.bug_report = os.path.join(self.test_dir, "bug_report.log")
        self.als_file = os.path.join(self.test_dir, "als.log")
        self.gen_file = os.path.join(self.test_dir, "gen.log")
        self.skip_file = os.path.join(self.test_dir, "skip.log")
        self.ops_file = os.path.join(self.test_dir, "ops.log")
        self.feedback_file = os.path.join(self.test_dir, "feedback.log")
        self.fix_file = os.path.join(self.test_dir, "fix.log")

        # Runtime files
        self.tmp_py = os.path.join(self.test_dir, "tmp.py")
        self.res_base_file = os.path.join(self.test_dir, "res_base.bin")
        self.res_target_file = os.path.join(self.test_dir, "res_target.bin")

        # Coverage files
        self.cov_base_file = os.path.join(self.test_dir, "base.coverage")
        self.cov_target_file = os.path.join(self.test_dir, "target.coverage")
        self.cov_rc_file = os.path.join(self.test_dir, ".coveragerc")

        # Compatibility: add crash_file attribute
        self.crash_file = os.path.join(self.test_dir, "crash.log")

        # Create coverage configuration file
        with open(self.cov_rc_file, "w") as f:
            print(self.cov_rc_file)
            f.write("[run]\nsource = ${TESTED_LIB_PATH}")

    def _setup_library_path(self):
        """Set up library path environment variable."""
        if self.lib == "pytorch":
            import torch

            lib_path = os.path.dirname(torch.__file__)
        elif self.lib == "tensorflow":
            import tensorflow as tf

            lib_path = os.path.dirname(tf.__file__)
        else:
            raise ValueError(f"Invalid library name: {self.lib}")

        os.environ["TESTED_LIB_PATH"] = lib_path
        return lib_path

    def write_file(self, filename: str, content: str, mode: str = "a+") -> bool:
        """Write content to a file."""
        try:
            with open(filename, mode, encoding="utf-8") as f:
                f.write(content + "\n")
            return True
        except Exception as e:
            print(f"Failed to write file {filename}: {e}")
            return False

    def read_file(self, filename: str) -> str:
        """Read content from a file."""
        try:
            if os.path.exists(filename):
                with open(filename, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            print(f"Failed to read file {filename}: {e}")
        return ""

    def remove_file(self, filename: str) -> bool:
        """Remove a file or directory."""
        try:
            if not os.path.exists(filename):
                return True

            if os.path.isdir(filename):
                shutil.rmtree(filename)
            else:
                os.remove(filename)
            return True
        except Exception as e:
            print(f"Failed to remove {filename}: {e}")
            print(
                "The folder deletion failed, possibly due to it being in use or insufficient permissions."
            )
            return False

    def open_file(self, filename: str, mode: str = "a+"):
        """Open a file."""
        return open(filename, mode, encoding="utf-8")

    def close_file(self, file_handle):
        """Close a file."""
        if hasattr(file_handle, "close"):
            file_handle.close()

    def batch_write(
        self, file_contents: Dict[str, str], mode: str = "a+"
    ) -> Dict[str, bool]:
        """Write multiple files in batch."""
        results = {}
        for filename, content in file_contents.items():
            results[filename] = self.write_file(filename, content, mode)
        return results


class FileMeta(type):
    """Metaclass for dynamic attribute access."""

    def __getattr__(cls, name):
        """Get attribute from instance when class attribute does not exist."""
        if hasattr(cls, "_instance") and cls._instance:
            instance = cls._instance
            if hasattr(instance, name):
                return getattr(instance, name)
        raise AttributeError(f"'{cls.__name__}' object has no attribute '{name}'")

    def __setattr__(cls, name, value):
        """Set attribute on instance if it is an instance attribute."""
        if hasattr(cls, "_instance") and cls._instance and hasattr(cls._instance, name):
            # For runtime state attributes, set on instance
            if name in ["cur_filename", "rendered_code", "eliminated_code"]:
                setattr(cls._instance, name, value)
                return
        super().__setattr__(name, value)


class File(metaclass=FileMeta):
    """File management class providing file operations and path management."""

    _instance: Optional[_SimpleFileManager] = None

    @classmethod
    def init(cls, root_dir, res_dir, output_dir, lib):
        """Initialize the file manager."""
        cls._instance = _SimpleFileManager(root_dir, res_dir, output_dir, lib)

    @classmethod
    def _get_instance(cls) -> _SimpleFileManager:
        """Get instance, ensuring it has been initialized."""
        if cls._instance is None:
            raise RuntimeError("File manager not initialized. Call File.init() first.")
        return cls._instance

    # Class method compatibility
    @classmethod
    def write_file(cls, filename, content, mode="a+"):
        """Write content to a file."""
        return cls._get_instance().write_file(filename, content, mode)

    @classmethod
    def read_file(cls, filename):
        """Read content from a file."""
        return cls._get_instance().read_file(filename)

    @classmethod
    def remove(cls, filename):
        """Remove a file or directory."""
        return cls._get_instance().remove_file(filename)

    @classmethod
    def open_file(cls, filename, mode="a+"):
        """Open a file."""
        return cls._get_instance().open_file(filename, mode)

    @classmethod
    def close_file(cls, file_handle):
        """Close a file."""
        return cls._get_instance().close_file(file_handle)

    @classmethod
    def get_library_path(cls):
        """Get library path."""
        return cls._get_instance()._setup_library_path()

    @classmethod
    def set_root_dir(cls, root_dir):
        """Set root directory."""
        if cls._instance:
            cls._instance.root_dir = root_dir

    # Batch operations
    @classmethod
    def batch_write(cls, file_contents: Dict[str, str], mode: str = "a+"):
        """Write multiple files in batch."""
        return cls._get_instance().batch_write(file_contents, mode)

    # Attribute delegation - automatic handling through __getattr__
    # These attributes are automatically delegated to instance through __getattr__ method
