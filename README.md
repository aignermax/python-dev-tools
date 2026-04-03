# Python Development Tools

Collection of productivity tools for .NET/C# and Python development. Designed to save tokens and improve AI agent efficiency.

## 🎯 Token Savings

These tools are optimized to reduce Claude Code token usage by filtering and summarizing output:
- **build_errors.py**: ~800 tokens saved vs raw `dotnet build`
- **smart_test.py**: ~1500 tokens saved vs raw `dotnet test`
- **semantic_search.py**: ~2000 tokens saved vs manual grep
- **find_symbol.py**: ~500 tokens saved vs full file reads
- **dotnet_deps.py**: ~600 tokens saved vs XML parsing

**Estimated total savings: 5000-10000 tokens per development session**

---

## Tools for .NET/C# Development

### 1. Build Errors Parser (`build_errors.py`)

Filters MSBuild output and provides fix suggestions for common C# errors.

**Features:**
- Parses `dotnet build` output, extracts only errors/warnings
- Provides fix suggestions for 20+ common C# error codes (CS0246, CS0103, etc.)
- Saves ~800 tokens vs raw build output
- Optional warnings display

**Usage:**
```bash
./build_errors.py [solution.sln]
./build_errors.py --warnings          # Include warnings
./build_errors.py MyApp.sln --raw     # Show raw output too
```

**Example Output:**
```
❌ ERRORS (2):
  [CS0246] ViewModels/MainViewModel.cs:15:12
    The type or namespace name 'ObservableObject' could not be found
    💡 Fix: Missing using directive or assembly reference. Add: using YourNamespace;
```

---

### 2. Find Symbol (`find_symbol.py`)

Fast C# symbol navigator using grep (no compilation needed).

**Features:**
- Find class/interface definitions
- Find method implementations
- Find all symbol usages
- Find interface implementations
- Works even if code doesn't compile

**Usage:**
```bash
./find_symbol.py class DesignCanvasViewModel
./find_symbol.py method PlaceComponent
./find_symbol.py usage ComponentLibrary
./find_symbol.py implements IComponent
```

**Example Output:**
```
Found 3 match(es):

📄 ViewModels/DesignCanvasViewModel.cs:45
   public partial class DesignCanvasViewModel : ObservableObject
```

---

### 3. .NET Dependency Analyzer (`dotnet_deps.py`)

NuGet package analyzer without XML parsing.

**Features:**
- List all packages across projects
- Check for outdated packages
- Find duplicate package versions
- Show dependency trees

**Usage:**
```bash
./dotnet_deps.py list              # All packages
./dotnet_deps.py outdated          # Check updates
./dotnet_deps.py duplicates        # Version conflicts
./dotnet_deps.py tree Avalonia     # Dependency tree
```

---

## Tools for Python/Generic Development

### 4. Semantic Search (`semantic_search.py`)

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

### 5. Smart Test Runner (`smart_test.py`)

Intelligent test runner for .NET/Python that filters and summarizes test output.

**Features:**
- Filters test output to show only failures/errors
- Provides concise summary instead of 1000+ lines
- Supports dotnet test, pytest, unittest
- Saves ~1500 tokens vs raw test output
- Smart detection of test frameworks

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
