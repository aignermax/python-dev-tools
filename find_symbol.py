#!/usr/bin/env python3
"""
C# Symbol Navigator

Fast grep-based symbol search for C# code without compilation.
Finds class definitions, method implementations, usages, etc.

Usage:
    ./find_symbol.py class <ClassName>           # Find class definition
    ./find_symbol.py method <MethodName>         # Find method definitions
    ./find_symbol.py usage <SymbolName>          # Find all usages
    ./find_symbol.py interface <InterfaceName>   # Find interface definition
    ./find_symbol.py implements <InterfaceName>  # Find implementing classes

Examples:
    ./find_symbol.py class DesignCanvasViewModel
    ./find_symbol.py method PlaceComponent
    ./find_symbol.py usage ComponentLibrary
    ./find_symbol.py implements IComponent
"""

import subprocess
import sys
import re
from pathlib import Path
from enum import Enum
from typing import List, Tuple

class SymbolType(Enum):
    CLASS = 'class'
    INTERFACE = 'interface'
    METHOD = 'method'
    PROPERTY = 'property'
    USAGE = 'usage'
    IMPLEMENTS = 'implements'

# Simple regex patterns for C# symbols
PATTERNS = {
    SymbolType.CLASS: r'class\s+{name}\b',
    SymbolType.INTERFACE: r'interface\s+{name}\b',
    SymbolType.METHOD: r'\w+\s+{name}\s*\(',  # Return type + name + (
    SymbolType.PROPERTY: r'\w+\s+{name}\s*[{{;]',  # Type + name + { or ;
    SymbolType.USAGE: r'\b{name}\b',  # Any word boundary
    SymbolType.IMPLEMENTS: r':\s*\w*{name}',  # : SomeClass, IInterface
}

def search_symbol(symbol_name: str, symbol_type: SymbolType, path: str = '.') -> List[Tuple[str, int, str]]:
    """
    Search for a symbol using ripgrep.

    Returns: List of (file_path, line_number, line_content)
    """
    pattern = PATTERNS[symbol_type].format(name=re.escape(symbol_name))

    # Use ripgrep if available, fallback to grep
    try:
        cmd = [
            'rg',
            '--line-number',
            '--no-heading',
            '--type', 'cs',
            pattern,
            path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to grep
        try:
            cmd = [
                'grep',
                '-rn',
                '--include=*.cs',
                '-E',
                pattern,
                path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stdout
        except subprocess.CalledProcessError:
            return []

    # Parse output
    results = []
    for line in output.splitlines():
        if ':' in line:
            parts = line.split(':', 2)
            if len(parts) >= 3:
                file_path = parts[0]
                try:
                    line_num = int(parts[1])
                    content = parts[2].strip()
                    results.append((file_path, line_num, content))
                except ValueError:
                    continue

    return results

def format_results(results: List[Tuple[str, int, str]], symbol_type: SymbolType):
    """Format and print search results"""
    if not results:
        print(f"No {symbol_type.value} found")
        return

    print(f"Found {len(results)} match(es):\n")

    for file_path, line_num, content in results:
        # Make file path relative for readability
        try:
            rel_path = Path(file_path).relative_to(Path.cwd())
        except ValueError:
            rel_path = file_path

        print(f"📄 {rel_path}:{line_num}")
        print(f"   {content}")
        print()

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()
    symbol_name = sys.argv[2]

    # Map command to symbol type
    type_map = {
        'class': SymbolType.CLASS,
        'interface': SymbolType.INTERFACE,
        'method': SymbolType.METHOD,
        'property': SymbolType.PROPERTY,
        'usage': SymbolType.USAGE,
        'implements': SymbolType.IMPLEMENTS,
    }

    if command not in type_map:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

    symbol_type = type_map[command]

    # Optional: search path argument
    search_path = sys.argv[3] if len(sys.argv) > 3 else '.'

    # Search
    results = search_symbol(symbol_name, symbol_type, search_path)

    # Display results
    format_results(results, symbol_type)

if __name__ == '__main__':
    main()
