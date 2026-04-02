#!/usr/bin/env python3
"""
Build Errors Parser for .NET Projects

Filters and analyzes dotnet build output, extracting errors and warnings
with helpful fix suggestions. Saves tokens vs raw build output.

Usage:
    ./build_errors.py [path/to/solution.sln]

Examples:
    ./build_errors.py                    # Build in current directory
    ./build_errors.py MyApp.sln          # Build specific solution
    ./build_errors.py --warnings         # Include warnings too
"""

import subprocess
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Common C# error codes with fix suggestions
COMMON_FIXES = {
    'CS0246': 'Missing using directive or assembly reference. Add: using YourNamespace; or install NuGet package',
    'CS0103': 'Name does not exist in current context. Check spelling or add using directive',
    'CS1061': 'Type does not contain definition. Check if method/property exists or add using',
    'CS0117': 'Type does not contain a definition. Verify member name spelling',
    'CS0234': 'Type or namespace does not exist. Check using directives and assembly references',
    'CS0029': 'Cannot implicitly convert type. Add explicit cast or change types',
    'CS0019': 'Operator cannot be applied to operands. Check operand types',
    'CS0266': 'Cannot convert type implicitly. Use explicit cast',
    'CS1503': 'Argument type mismatch. Check method signature',
    'CS0120': 'Object reference required for non-static member. Create instance or make member static',
    'CS0101': 'Namespace already contains definition. Remove duplicate or rename',
    'CS0122': 'Member is inaccessible due to protection level. Change access modifier or use different member',
    'CS0229': 'Ambiguous reference between two members. Use fully qualified name',
    'CS0311': 'Type cannot be used as type parameter. Check generic constraints',
    'CS0051': 'Inconsistent accessibility. Make parameter type as accessible as method',
    'CS0060': 'Inconsistent accessibility in base class',
    'CS0115': 'No suitable method found to override. Check base class method signature',
    'CS0508': 'Return type must match overridden member',
    'CS0111': 'Type already defines member with same signature. Rename or remove duplicate',
    'CS1729': 'Type does not contain constructor. Add matching constructor to base class',
}

class BuildError:
    """Represents a single build error or warning"""
    def __init__(self, file: str, line: int, col: int, code: str, message: str, severity: str):
        self.file = file
        self.line = line
        self.col = col
        self.code = code
        self.message = message
        self.severity = severity  # 'error' or 'warning'

    def __str__(self):
        location = f"{self.file}:{self.line}:{self.col}" if self.line else self.file
        fix = COMMON_FIXES.get(self.code, '')
        fix_text = f"\n    💡 Fix: {fix}" if fix else ''
        return f"  [{self.code}] {location}\n    {self.message}{fix_text}"

def parse_build_output(output: str, include_warnings: bool = False) -> List[BuildError]:
    """Parse MSBuild output and extract errors/warnings"""
    errors = []

    # Pattern: path/file.cs(line,col): error CS1234: message
    pattern = r'([^(]+)\((\d+),(\d+)\):\s+(error|warning)\s+([A-Z]+\d+):\s+(.+)'

    for line in output.splitlines():
        match = re.search(pattern, line)
        if match:
            file, line_num, col, severity, code, message = match.groups()

            if severity == 'warning' and not include_warnings:
                continue

            errors.append(BuildError(
                file=file.strip(),
                line=int(line_num),
                col=int(col),
                code=code,
                message=message.strip(),
                severity=severity
            ))

    return errors

def run_build(solution_path: str = None) -> Tuple[str, int]:
    """Run dotnet build and return (output, exit_code)"""
    cmd = ['dotnet', 'build']
    if solution_path:
        cmd.append(solution_path)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path.cwd()
    )

    return result.stdout + result.stderr, result.returncode

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Parse and filter .NET build errors')
    parser.add_argument('solution', nargs='?', help='Path to solution file')
    parser.add_argument('--warnings', '-w', action='store_true', help='Include warnings')
    parser.add_argument('--raw', action='store_true', help='Show raw output too')

    args = parser.parse_args()

    print("🔨 Building project...")
    output, exit_code = run_build(args.solution)

    if args.raw:
        print("\n" + "="*60)
        print("RAW OUTPUT:")
        print("="*60)
        print(output)
        print("="*60 + "\n")

    errors = parse_build_output(output, include_warnings=args.warnings)

    # Group by severity
    error_list = [e for e in errors if e.severity == 'error']
    warning_list = [e for e in errors if e.severity == 'warning']

    print(f"\n📊 Build Summary:")
    print(f"  Errors: {len(error_list)}")
    print(f"  Warnings: {len(warning_list)}")

    if error_list:
        print(f"\n❌ ERRORS ({len(error_list)}):")
        for error in error_list:
            print(error)

    if warning_list and args.warnings:
        print(f"\n⚠️  WARNINGS ({len(warning_list)}):")
        for warning in warning_list:
            print(warning)

    if not errors:
        print("\n✅ Build successful - no errors or warnings!")

    # Exit with same code as build
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
