#!/bin/bash
# python-dev-tools installer — fetches every script in this repo into
# $HOME/.cap-tools/ and (optionally) sets up a venv with the runtime
# dependencies semantic_search.py needs.
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/aignermax/python-dev-tools/main/install.sh | bash
#   curl -sSL https://raw.githubusercontent.com/aignermax/python-dev-tools/main/install.sh | bash -s -- --no-venv
#
# Flags:
#   --no-venv    Skip the venv creation; assume openai/dotenv are reachable
#                from the system python3.

# `pipefail` is critical here — without it, a failing `curl` piped into
# `tr` would still exit 0 because only `tr`'s exit status counts, and
# we'd silently install empty executables on a 404.
set -e
set -o pipefail

VERSION="2.0.0"
INSTALL_DIR="$HOME/.cap-tools"
REPO_URL="https://raw.githubusercontent.com/aignermax/python-dev-tools"
BRANCH="main"
SKIP_VENV=0

for arg in "$@"; do
    case "$arg" in
        --no-venv) SKIP_VENV=1 ;;
        --branch=*) BRANCH="${arg#--branch=}" ;;
        --help|-h)
            echo "Usage: install.sh [--no-venv] [--branch=NAME]"
            exit 0
            ;;
        *)
            echo "WARN: ignoring unknown argument: $arg" >&2
            ;;
    esac
done

echo "🔧 python-dev-tools installer v$VERSION"
echo "   target: $INSTALL_DIR"
echo "   branch: $BRANCH"
echo ""

mkdir -p "$INSTALL_DIR"

# Every executable in the repo. README is fetched as documentation.
# Adding a new tool? Just append to this list.
TOOLS=(
    "semantic_search.py"
    "smart_test.py"
    "build_errors.py"
    "dotnet_deps.py"
    "find_symbol.py"
)

echo "📦 Fetching tools..."
for tool in "${TOOLS[@]}"; do
    echo "  - $tool"
    # Strip CRLF on download — GitHub's raw endpoint preserves whatever
    # line endings are in the blob, and a stray \r in the shebang breaks
    # `#!/usr/bin/env python3` on Linux.
    # `-f` makes curl exit non-zero on HTTP errors (404, 500). Combined with
    # `set -o pipefail` above, a missing tool aborts the install instead of
    # producing a zero-byte executable.
    curl -fsSL "$REPO_URL/$BRANCH/$tool" | tr -d '\r' > "$INSTALL_DIR/$tool"
    chmod +x "$INSTALL_DIR/$tool"
done

curl -fsSL "$REPO_URL/$BRANCH/README.md" | tr -d '\r' > "$INSTALL_DIR/README.md"

echo ""
echo "🐍 Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found. Install Python 3.8+ and re-run." >&2
    exit 1
fi
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "   python3: $PYTHON_VERSION"

if [ "$SKIP_VENV" = "1" ]; then
    echo ""
    echo "⏩ --no-venv passed; skipping venv setup."
    echo "   Make sure openai and python-dotenv are importable from python3."
else
    VENV_DIR="$INSTALL_DIR/venv"
    if [ ! -d "$VENV_DIR" ]; then
        echo ""
        echo "🧪 Creating venv at $VENV_DIR..."
        python3 -m venv "$VENV_DIR"
    else
        echo ""
        echo "🧪 Reusing existing venv at $VENV_DIR"
    fi

    echo "   installing openai, python-dotenv..."
    # No --quiet: pip's own error messages are the most useful signal when
    # an install fails (offline, proxy, PEP 668), and `set -e` will abort
    # the script anyway, so silencing them just hides the diagnosis.
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install openai python-dotenv

    # Point semantic_search.py's shebang at the venv so users can invoke
    # the script directly (`~/.cap-tools/semantic_search.py "query"`)
    # without remembering to source the venv first.
    SHEBANG="#!$VENV_DIR/bin/python3"
    SEARCH_FILE="$INSTALL_DIR/semantic_search.py"
    # Replace the first line in-place. Use a temp file to keep this
    # portable across BSD/GNU sed.
    { echo "$SHEBANG"; tail -n +2 "$SEARCH_FILE"; } > "$SEARCH_FILE.tmp"
    mv "$SEARCH_FILE.tmp" "$SEARCH_FILE"
    chmod +x "$SEARCH_FILE"
    echo "   semantic_search.py shebang -> $VENV_DIR/bin/python3"
fi

echo ""
echo "✅ Installed:"
for tool in "${TOOLS[@]}"; do
    echo "   $INSTALL_DIR/$tool"
done

echo ""
echo "📝 Next steps:"
echo "   1. Set OPENAI_API_KEY (in your project's .env or your shell)"
echo "      for semantic_search.py."
echo "   2. Reference the tools in your CLAUDE.md so the agent knows they exist."
echo ""
echo "Smoke tests:"
echo "   $INSTALL_DIR/find_symbol.py class FooBar"
echo "   $INSTALL_DIR/smart_test.py --help"
echo "   $INSTALL_DIR/semantic_search.py 'where is the main entry point?'"
