#!/usr/bin/env python3

"""
This file was the original combined E2E test file.
The tests have been split into separate files:

- test_e2e_list_tools.py - Tests for listing available tools
- test_e2e_read_file.py - Tests for reading files
- test_e2e_write_file.py - Tests for writing files
- test_e2e_edit_file.py - Tests for editing files
- test_e2e_ls.py - Tests for listing directories
- test_e2e_run_tests.py - Tests for running tests
- test_e2e_format.py - Tests for formatting code
- test_e2e_security.py - Tests for security aspects

Please refer to those files for the individual tests.
"""

import unittest

from codemcp import MCPEndToEndTestCase


class DeprecatedTest(MCPEndToEndTestCase):
    """This test class is deprecated. Tests have been moved to separate files."""

    async def test_deprecated(self):
        """This test is deprecated."""
        print("This test file is deprecated. Tests have been moved to separate files.")
        self.assertTrue(True, "This test is deprecated")


if __name__ == "__main__":
    unittest.main()
