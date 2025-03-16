#!/usr/bin/env python3

import asyncio
import os

from expecttest import TestCase

from codemcp.testing import GitRepo
from codemcp.tools.read_file import read_file_content
from codemcp.tools.user_prompt import user_prompt


class TestCursorRules(TestCase):
    async def asyncSetUp(self):
        # Create a temporary git repository
        self.repo = GitRepo()
        self.repo_dir = self.repo.path

        # Create .cursor/rules directory structure
        self.rules_dir = os.path.join(self.repo_dir, ".cursor", "rules")
        os.makedirs(self.rules_dir, exist_ok=True)

        # Create test files
        self.create_test_files()

    async def asyncTearDown(self):
        # Clean up the temporary repository
        self.repo.cleanup()

    def create_test_files(self):
        # Create a test JavaScript file
        js_file_path = os.path.join(self.repo_dir, "test.js")
        with open(js_file_path, "w") as f:
            f.write("// This is a test JavaScript file\nconsole.log('Hello world');\n")

        # Create a test Python file
        py_file_path = os.path.join(self.repo_dir, "test.py")
        with open(py_file_path, "w") as f:
            f.write("# This is a test Python file\nprint('Hello world')\n")

        # Create an MDC file for JavaScript files
        js_rule_path = os.path.join(self.rules_dir, "javascript.mdc")
        with open(js_rule_path, "w") as f:
            f.write(
                """---
description: For JavaScript files
globs: *.js,**/*.jsx
alwaysApply: false
---
Use camelCase for variable names in JavaScript.
"""
            )

        # Create an MDC file for Python files
        py_rule_path = os.path.join(self.rules_dir, "python.mdc")
        with open(py_rule_path, "w") as f:
            f.write(
                """---
description: For Python files
globs: *.py
alwaysApply: false
---
Use snake_case for variable names in Python.
"""
            )

        # Create an MDC file that always applies
        always_rule_path = os.path.join(self.rules_dir, "always.mdc")
        with open(always_rule_path, "w") as f:
            f.write(
                """---
description: General coding guidelines
alwaysApply: true
---
Follow PEP 8 guidelines for Python code and use descriptive variable names.
"""
            )

        # Create an MDC file with just a description
        desc_rule_path = os.path.join(self.rules_dir, "suggested.mdc")
        with open(desc_rule_path, "w") as f:
            f.write(
                """---
description: For code that needs optimization
globs: 
alwaysApply: false
---
Consider time and space complexity when writing algorithms.
"""
            )

    async def test_read_file_with_rules(self):
        # Test reading a JavaScript file
        js_file_path = os.path.join(self.repo_dir, "test.js")
        result = await read_file_content(js_file_path)

        # Verify that the JavaScript rule was applied
        self.assertIn("// .cursor/rules results:", result)
        self.assertIn("Use camelCase for variable names in JavaScript", result)

        # Verify that the always-apply rule was applied
        self.assertIn("Follow PEP 8 guidelines", result)

        # Verify that the suggested rule appears
        self.assertIn("If For code that needs optimization applies", result)

        # Test reading a Python file
        py_file_path = os.path.join(self.repo_dir, "test.py")
        result = await read_file_content(py_file_path)

        # Verify that the Python rule was applied
        self.assertIn("// .cursor/rules results:", result)
        self.assertIn("Use snake_case for variable names in Python", result)

        # Verify that the always-apply rule was applied
        self.assertIn("Follow PEP 8 guidelines", result)

    async def test_user_prompt_with_rules(self):
        # Test user prompt with rules
        result = await user_prompt("Test prompt")

        # Verify that the always-apply rule was applied
        self.assertIn("// .cursor/rules results:", result)
        self.assertIn("Follow PEP 8 guidelines", result)

        # Verify that the suggested rule appears
        self.assertIn("If For code that needs optimization applies", result)


if __name__ == "__main__":
    asyncio.run(TestCursorRules().test_read_file_with_rules())
    asyncio.run(TestCursorRules().test_user_prompt_with_rules())
