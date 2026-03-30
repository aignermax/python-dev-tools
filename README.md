# Python Development Tools

Collection of AI-powered Python development tools designed to enhance your development workflow.

## Tools Included

### 1. Semantic Search (`semantic_search.py`)

AI-powered semantic code search using OpenAI embeddings.

**Features:**
- Natural language code search (e.g., "function that validates email addresses")
- Finds semantically similar code, not just keyword matches
- Caches embeddings for fast repeated searches
- Supports Python, JavaScript, TypeScript, Java, C++, Go, Rust

**Usage:**
```bash
python semantic_search.py "your search query"
```

**Requirements:**
- OpenAI API key in environment variable `OPENAI_API_KEY`
- Python packages: `openai`, `numpy`

**Examples:**
```bash
# Find authentication logic
python semantic_search.py "user authentication and login"

# Find error handling
python semantic_search.py "exception handling and error recovery"

# Find API endpoints
python semantic_search.py "REST API routes and handlers"
```

### 2. Smart Test Runner (`smart_test.py`)

Intelligent test runner that automatically finds and runs relevant tests based on your code changes.

**Features:**
- Detects changed files in your Git repository
- Uses AI to identify related test files
- Automatically runs only relevant tests
- Supports pytest, unittest, and other Python test frameworks
- Falls back to running all tests if no changes detected

**Usage:**
```bash
# Run tests for changed files
python smart_test.py

# Specify custom test directory
python smart_test.py --test-dir tests/

# Force run all tests
python smart_test.py --all
```

**Requirements:**
- OpenAI API key in environment variable `OPENAI_API_KEY`
- Python packages: `openai`, `pytest` (or your preferred test runner)
- Git repository

**How it works:**
1. Detects uncommitted/unstaged changes in Git
2. Uses AI to determine which test files are relevant
3. Runs only those specific tests
4. Shows clear results and saves time

## Installation

1. Clone this repository:
```bash
git clone https://github.com/Akhetonics/python-dev-tools.git
cd python-dev-tools
```

2. Install required packages:
```bash
pip install openai numpy pytest
```

3. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

4. Run the tools:
```bash
python semantic_search.py "your query"
python smart_test.py
```

## Integration with CI/CD

These tools can be integrated into your CI/CD pipeline:

**GitHub Actions example:**
```yaml
- name: Run smart tests
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: python smart_test.py
```

## Integration with Autonomous Issue Agent

These tools are designed to work seamlessly with the [Autonomous Issue Agent](https://github.com/Akhetonics/autonomous-issue-agent), which can automatically use them to:
- Search codebases semantically when implementing features
- Run only relevant tests after making changes
- Improve development efficiency

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or pull request.

## Version History

See [Releases](https://github.com/Akhetonics/python-dev-tools/releases) for version history.
