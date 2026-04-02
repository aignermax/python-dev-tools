#!/usr/bin/env python3
"""
.NET Dependency Analyzer

Analyzes NuGet packages without parsing XML directly.
Uses dotnet CLI commands for package information.

Usage:
    ./dotnet_deps.py list              # List all packages
    ./dotnet_deps.py outdated          # Check for updates
    ./dotnet_deps.py duplicates        # Find duplicate package references
    ./dotnet_deps.py tree <package>    # Show dependency tree for a package

Examples:
    ./dotnet_deps.py list
    ./dotnet_deps.py outdated
    ./dotnet_deps.py duplicates
    ./dotnet_deps.py tree Avalonia
"""

import subprocess
import sys
import re
from pathlib import Path
from collections import defaultdict
from typing import List, Dict

def run_command(cmd: List[str]) -> str:
    """Run a command and return its output"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return ""

def list_packages():
    """List all NuGet packages in the solution"""
    print("📦 Listing all NuGet packages...\n")

    output = run_command(['dotnet', 'list', 'package'])

    if not output:
        print("No packages found or error occurred")
        return

    # Parse output
    # Format: Project 'path' has the following package references
    #    [netX.X]:
    #    > PackageName    Version

    current_project = None
    packages = defaultdict(list)

    for line in output.splitlines():
        line = line.strip()

        if line.startswith('Project'):
            # Extract project name from path
            match = re.search(r"'([^']+)'", line)
            if match:
                proj_path = match.group(1)
                current_project = Path(proj_path).stem
        elif line.startswith('>'):
            # Package reference
            parts = line[1:].split()
            if len(parts) >= 2:
                pkg_name = parts[0]
                version = parts[1]
                if current_project:
                    packages[current_project].append((pkg_name, version))

    # Display
    for project, pkgs in sorted(packages.items()):
        print(f"📁 {project} ({len(pkgs)} packages):")
        for name, version in sorted(pkgs):
            print(f"   • {name:40} {version}")
        print()

def check_outdated():
    """Check for outdated packages"""
    print("🔍 Checking for outdated packages...\n")

    output = run_command(['dotnet', 'list', 'package', '--outdated'])

    if not output:
        print("All packages are up-to-date or error occurred")
        return

    # Parse output
    updates_found = False
    for line in output.splitlines():
        if '>' in line and 'Latest' in line:
            updates_found = True
            break

    if not updates_found:
        print("✅ All packages are up-to-date!")
        return

    print("⚠️  Outdated packages found:\n")
    print(output)

def find_duplicates():
    """Find duplicate package references across projects"""
    print("🔎 Finding duplicate package references...\n")

    output = run_command(['dotnet', 'list', 'package'])

    if not output:
        print("No packages found")
        return

    # Track package versions across projects
    package_versions = defaultdict(lambda: defaultdict(list))

    current_project = None
    for line in output.splitlines():
        line = line.strip()

        if line.startswith('Project'):
            match = re.search(r"'([^']+)'", line)
            if match:
                proj_path = match.group(1)
                current_project = Path(proj_path).stem
        elif line.startswith('>'):
            parts = line[1:].split()
            if len(parts) >= 2:
                pkg_name = parts[0]
                version = parts[1]
                if current_project:
                    package_versions[pkg_name][version].append(current_project)

    # Find packages with multiple versions
    duplicates = {
        pkg: versions
        for pkg, versions in package_versions.items()
        if len(versions) > 1
    }

    if not duplicates:
        print("✅ No duplicate package versions found!")
        return

    print(f"⚠️  Found {len(duplicates)} packages with version conflicts:\n")

    for pkg, versions in sorted(duplicates.items()):
        print(f"📦 {pkg}:")
        for version, projects in sorted(versions.items()):
            print(f"   v{version}:")
            for proj in projects:
                print(f"      • {proj}")
        print()

def show_dependency_tree(package_name: str):
    """Show dependency tree for a specific package"""
    print(f"🌳 Dependency tree for {package_name}...\n")

    # Try to find projects that reference this package
    output = run_command(['dotnet', 'list', 'package'])

    projects_with_pkg = []
    current_project = None

    for line in output.splitlines():
        line = line.strip()

        if line.startswith('Project'):
            match = re.search(r"'([^']+)'", line)
            if match:
                current_project = match.group(1)
        elif line.startswith('>') and package_name.lower() in line.lower():
            if current_project:
                projects_with_pkg.append(current_project)

    if not projects_with_pkg:
        print(f"Package '{package_name}' not found in any project")
        return

    print(f"Found in {len(projects_with_pkg)} project(s):\n")

    for proj in projects_with_pkg:
        print(f"📁 {Path(proj).stem}")

        # Get dependencies for this specific project
        tree_output = run_command(['dotnet', 'list', proj, 'package', '--include-transitive'])

        # Filter for the specific package and its dependencies
        in_package = False
        for line in tree_output.splitlines():
            if package_name.lower() in line.lower():
                in_package = True
                print(f"   {line}")
            elif in_package and line.strip().startswith('>'):
                # This might be a transitive dependency
                print(f"   {line}")

        print()

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'list':
        list_packages()
    elif command == 'outdated':
        check_outdated()
    elif command == 'duplicates':
        find_duplicates()
    elif command == 'tree':
        if len(sys.argv) < 3:
            print("Usage: ./dotnet_deps.py tree <package_name>")
            sys.exit(1)
        show_dependency_tree(sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()
