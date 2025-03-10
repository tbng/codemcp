BIGGEST PROBLEMS
- Increasing the success rate of code patching
  - Logging so I can repro these problems
- Branchy git structure for ease of review
- Fix the asyncio testing



- Prevent edits to files which are not under version control
- Add files to context
- Set a base directory (so absolute paths aren't always required)
- Import Aider system prompts
- Load webpages
- Run tests/lints/typecheck

- LS - only use git ls-files
- An "init" command that will feed the project prompt (per project config)
- Add a system prompt command that will load instructions at the start of
  convo

- Deal with output length limit from Claude Desktop (cannot do an edit longer
  than the limit)
- More faithfully copy claude code's line numbering algorithm
- Stop using catch all exceptions
- Mocks - SUSPICOUS
- Use the Anthropic export data to do some token counting
