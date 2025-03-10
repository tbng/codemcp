BIGGEST PROBLEMS
- Branchy git structure for ease of review
  - This is less pressing now with the 'git diff origin/main' trick
- Audit the tests to make sure they actually do the right thing

CODE QUAL
- Whenever we do a subprocess call, we MUST log the stdout/stderr
  - Add a wrapper here to make sure this consistently happens
- Setup types
- General logging to repro problems
- Stop using catch all exceptions

TOOLS:
- ✅ Linter/autoformatter integration
- Typecheck/build integration
- Test runner integration
- Scrape webpage and add to context
- Explicitly add file to context
- Make file executable tool
- A few more of Claude Code's tools: glob, memory, notebook

FEATURES
- Diff review mode

HARD TO FIX
- Deal with output length limit from Claude Desktop (cannot do an edit longer
  than the limit)

SHARPEN THE SAW
- Use the Anthropic export data to do some token counting / analysis

UNCLEAR PAYOFF
- More faithfully copy claude code's line numbering algorithm
- Figure out if "compact output" is a good idea
- Figure out how to make Claude stop trying to do things I don't want it to do
  (like running tests)

LLM AFFORDANCE
- Support this style of grep
{
  `command`: `Grep`,
  `pattern`: `self\\.assertIn.*normalized_result`,
  `path`: `/Users/ezyang/Dev/codemcp/test/test_mcp_e2e.py`
}
- Figure out how to stop LLM from creating lots of random shell scripts to try
  to execute commands
- Regex search replace for refactor-y stuff (need to prompt this well, cuz LLM
  needs to review changes)
