#!/usr/bin/env python3

"""Unit tests for the common module."""

import unittest
from unittest.mock import patch

from codemcp.common import normalize_file_path


class CommonTest(unittest.TestCase):
    """Test for functions in the common module."""

    def test_normalize_file_path_tilde_expansion(self):
        """Test that normalize_file_path properly expands the tilde character."""
        # Mock expanduser to return a known path
        with patch("os.path.expanduser") as mock_expanduser:
            # Setup the mock to replace ~ with a specific path
            mock_expanduser.side_effect = lambda p: p.replace("~", "/home/testuser")

            # Test with a path that starts with a tilde
            result = normalize_file_path("~/test_dir")

            # Verify expanduser was called with the tilde path
            mock_expanduser.assert_called_with("~/test_dir")

            # Verify the result has the tilde expanded
            self.assertEqual(result, "/home/testuser/test_dir")

            # Test with a path that doesn't have a tilde
            result = normalize_file_path("/absolute/path")

            # Verify expanduser was still called for consistency
            mock_expanduser.assert_called_with("/absolute/path")

            # Verify absolute path is unchanged
            self.assertEqual(result, "/absolute/path")

            # Test with a relative path (no tilde)
            with patch("os.getcwd") as mock_getcwd:
                mock_getcwd.return_value = "/current/dir"
                result = normalize_file_path("relative/path")

                # Verify expanduser was called with the relative path
                mock_expanduser.assert_called_with("relative/path")

                # Verify the result is an absolute path
                self.assertEqual(result, "/current/dir/relative/path")


if __name__ == "__main__":
    unittest.main()
