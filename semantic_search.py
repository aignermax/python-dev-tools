#!/usr/bin/env python3
"""
Semantic Code Search Tool for Autonomous Agent

Simple semantic search over codebase using OpenAI embeddings.
Can be called from agent via Bash - no MCP needed!

Usage:
    python semantic_search.py "find ViewModel for parameter sweeping"
    python semantic_search.py "where is the bounding box calculation logic?"
    python semantic_search.py "test files for analysis features"
"""

import os
import re
import sys
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple
import openai
from dotenv import load_dotenv

# Load environment variables. Try multiple locations so the tool works
# regardless of how it was installed (alongside a project, in a tools/ subdir,
# or at a fixed user-global path with the project two directories away).
_env_candidates = [
    Path.cwd() / ".env",                    # repo root — most common when run from a project
    Path(__file__).parent / ".env",         # next to the tool itself
    Path(__file__).parent.parent / ".env",  # one level up from the tool
]
_env_loaded = False
for _env_candidate in _env_candidates:
    if _env_candidate.exists():
        load_dotenv(_env_candidate)
        _env_loaded = True
        break
if not _env_loaded and not os.environ.get("OPENAI_API_KEY"):
    print(
        "WARN: no .env found and OPENAI_API_KEY is not set. Tried: "
        + ", ".join(str(p) for p in _env_candidates),
        file=sys.stderr,
    )

# Configuration
CACHE_DIR = Path(__file__).parent / ".search_cache"
INDEX_FILE = CACHE_DIR / "code_index.json"
EMBEDDING_MODEL = "text-embedding-3-small"  # Cheap and fast
TOP_K = 5  # Return top 5 results

# File patterns to index
INCLUDE_PATTERNS = [
    "**/*.cs",      # C# files
    "**/*.axaml",   # Avalonia XAML
    "**/*.md",      # Documentation
]

EXCLUDE_PATTERNS = [
    "**/bin/**",
    "**/obj/**",
    "**/.git/**",
    "**/node_modules/**",
]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    return dot_product / (norm_a * norm_b) if norm_a and norm_b else 0.0


def get_file_hash(path: Path) -> str:
    """Get hash of file for caching."""
    return hashlib.md5(path.read_bytes()).hexdigest()


def should_index_file(path: Path, repo_root: Path) -> bool:
    """Check if file should be indexed."""
    rel_path = path.relative_to(repo_root)

    # Check exclusions
    for pattern in EXCLUDE_PATTERNS:
        if rel_path.match(pattern):
            return False

    # Check inclusions
    for pattern in INCLUDE_PATTERNS:
        if rel_path.match(pattern):
            return True

    return False


def extract_code_chunks(file_path: Path) -> List[Dict[str, str]]:
    """Extract meaningful chunks from a code file."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except:
        return []

    if file_path.suffix == '.cs':
        return _chunk_csharp(file_path, content)
    if file_path.suffix == '.axaml':
        return _chunk_axaml(file_path, content)
    # Other files (e.g. .md): single truncated chunk
    return [{
        'file': str(file_path),
        'lines': '1-end',
        'content': content[:5000],
    }]


def _chunk_csharp(file_path: Path, content: str) -> List[Dict[str, str]]:
    """Chunk C# files at class/method boundaries."""
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    chunk_start_line = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if any(kw in stripped for kw in ['class ', 'interface ', 'public ', 'private ', 'protected ']):
            if current_chunk:
                chunks.append({
                    'file': str(file_path),
                    'lines': f"{chunk_start_line}-{i}",
                    'content': '\n'.join(current_chunk[:50]),
                })
            current_chunk = [line]
            chunk_start_line = i + 1
        else:
            current_chunk.append(line)

    if current_chunk:
        chunks.append({
            'file': str(file_path),
            'lines': f"{chunk_start_line}-{len(lines)}",
            'content': '\n'.join(current_chunk[:50]),
        })
    return chunks


# Top-level AXAML elements that mark a logical section boundary.
_AXAML_TOP_LEVEL_TAGS = (
    'Window.Resources', 'Window.Styles', 'Window.KeyBindings',
    'UserControl.Resources', 'UserControl.Styles', 'UserControl.KeyBindings',
    'Application.Resources', 'Application.Styles',
    'DockPanel', 'Grid', 'StackPanel', 'TabControl', 'TabItem',
    'ScrollViewer', 'Border', 'Panel', 'SplitView',
)
_AXAML_BINDING_RE = re.compile(r'\{Binding[^}]+\}|\{CompiledBinding[^}]+\}|x:DataType\s*=\s*"[^"]+"|x:Class\s*=\s*"[^"]+"|x:Name\s*=\s*"[^"]+"')


def _chunk_axaml(file_path: Path, content: str) -> List[Dict[str, str]]:
    """Chunk AXAML files into header, structural sections, and a binding index.

    AXAML files are XML; semantically meaningful units are the root element header
    (with namespaces and DataType), top-level structural blocks, and bindings.
    Binding extraction creates a compact searchable index without re-reading the file.
    """
    lines = content.split('\n')
    chunks: List[Dict[str, str]] = []

    # The header chunk gets its own embedding because namespaces and
    # x:DataType determine which ViewModel a search query should match —
    # losing them in a generic body chunk hurts retrieval.
    header_end = content.find('>')
    header_line_count = 0
    if header_end != -1:
        header_text = content[:header_end + 1]
        header_line_count = header_text.count('\n') + 1
        chunks.append({
            'file': str(file_path),
            'lines': f"1-{header_line_count}",
            'content': header_text[:3000],
        })

    # Section start = top-level tag with <=8 leading spaces. The indent guard
    # avoids false positives when the same tag name appears nested inside
    # a control template.
    section_start = header_line_count
    section_lines: List[str] = []
    for i, line in enumerate(lines[header_line_count:], start=header_line_count):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        is_section = (
            indent <= 8
            and stripped.startswith('<')
            and any(stripped.startswith(f'<{tag}') for tag in _AXAML_TOP_LEVEL_TAGS)
        )
        if is_section and section_lines:
            section_text = '\n'.join(section_lines)
            if section_text.strip():
                chunks.append({
                    'file': str(file_path),
                    'lines': f"{section_start + 1}-{i}",
                    'content': section_text[:4000],
                })
            section_lines = [line]
            section_start = i
        else:
            section_lines.append(line)

    if section_lines:
        section_text = '\n'.join(section_lines)
        if section_text.strip():
            chunks.append({
                'file': str(file_path),
                'lines': f"{section_start + 1}-{len(lines)}",
                'content': section_text[:4000],
            })

    # One additional chunk that concentrates every binding/x:* attribute,
    # so a single embedding covers all data-binding surfaces of the file
    # (queries like "binding for SomeViewModel" then need only one chunk hit).
    bindings = _AXAML_BINDING_RE.findall(content)
    if bindings:
        seen = set()
        unique_bindings = []
        for b in bindings:
            if b not in seen:
                seen.add(b)
                unique_bindings.append(b)
        chunks.append({
            'file': str(file_path),
            'lines': '1-end (bindings)',
            'content': '\n'.join(unique_bindings)[:4000],
        })

    return chunks


def build_index(repo_root: Path, force_rebuild: bool = False) -> Dict:
    """Build or load code index with embeddings."""
    CACHE_DIR.mkdir(exist_ok=True)

    # Check if index exists and is fresh
    if INDEX_FILE.exists() and not force_rebuild:
        print(f"Loading existing index from {INDEX_FILE}", file=sys.stderr)
        with open(INDEX_FILE, 'r') as f:
            return json.load(f)

    print(f"Building code index for {repo_root}...", file=sys.stderr)

    # Find all code files
    code_files = []
    for pattern in INCLUDE_PATTERNS:
        code_files.extend(repo_root.glob(pattern))

    code_files = [f for f in code_files if should_index_file(f, repo_root)]

    print(f"Found {len(code_files)} files to index", file=sys.stderr)

    # Extract chunks
    all_chunks = []
    for file_path in code_files:
        chunks = extract_code_chunks(file_path)
        all_chunks.extend(chunks)

    print(f"Extracted {len(all_chunks)} code chunks", file=sys.stderr)

    # Get embeddings (batch for efficiency)
    if not os.environ.get('OPENAI_API_KEY'):
        print("ERROR: OPENAI_API_KEY not set. Cannot create embeddings.", file=sys.stderr)
        sys.exit(1)

    client = openai.OpenAI()

    print(f"Computing embeddings...", file=sys.stderr)
    texts = [chunk['content'] for chunk in all_chunks]

    # OpenAI rejects embedding requests above 300K tokens. Tokens are
    # roughly chars/4 for English-ish input but can be denser for source
    # code, so we cap on chars conservatively: 280K chars ≈ 70K-280K
    # tokens depending on tokenisation, leaving comfortable headroom under
    # the 300K limit. The 2048 item cap is OpenAI's per-request maximum.
    MAX_ITEMS_PER_BATCH = 2048
    MAX_CHARS_PER_BATCH = 280_000
    all_embeddings = []
    batch: List[str] = []
    batch_chars = 0
    batch_num = 0

    def flush_batch() -> None:
        nonlocal batch_chars, batch_num
        if not batch:
            return
        batch_num += 1
        print(f"  Batch {batch_num} ({len(batch)} items, {batch_chars} chars)", file=sys.stderr)
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        all_embeddings.extend([item.embedding for item in response.data])
        batch.clear()
        batch_chars = 0

    for text in texts:
        text_len = len(text)
        # A single chunk that already exceeds the per-batch char budget would
        # be rejected by OpenAI on its own. Truncate defensively — chunkers
        # currently cap at 5000 chars so this branch is unreachable today,
        # but the guard prevents future chunker changes from regressing here.
        if text_len > MAX_CHARS_PER_BATCH:
            text = text[:MAX_CHARS_PER_BATCH]
            text_len = MAX_CHARS_PER_BATCH
        if batch and (len(batch) >= MAX_ITEMS_PER_BATCH or batch_chars + text_len > MAX_CHARS_PER_BATCH):
            flush_batch()
        batch.append(text)
        batch_chars += text_len
    flush_batch()

    # Build index
    index = {
        'chunks': all_chunks,
        'embeddings': all_embeddings,
        'repo_root': str(repo_root),
        'num_files': len(code_files),
        'num_chunks': len(all_chunks)
    }

    # Save index
    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f)

    print(f"Index saved to {INDEX_FILE}", file=sys.stderr)
    return index


def search(query: str, index: Dict, top_k: int = TOP_K) -> List[Tuple[str, float, str]]:
    """Search for relevant code chunks."""
    # Get query embedding
    client = openai.OpenAI()

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query
    )
    query_embedding = response.data[0].embedding

    # Compute similarities
    similarities = []
    for i, chunk_embedding in enumerate(index['embeddings']):
        sim = cosine_similarity(query_embedding, chunk_embedding)
        similarities.append((i, sim))

    # Sort by similarity
    similarities.sort(key=lambda x: x[1], reverse=True)

    # Return top-k results
    results = []
    for i, sim in similarities[:top_k]:
        chunk = index['chunks'][i]
        results.append((
            chunk['file'],
            sim,
            chunk['lines']
        ))

    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: semantic_search.py <query>", file=sys.stderr)
        print("Example: semantic_search.py 'find ViewModel for analysis features'", file=sys.stderr)
        sys.exit(1)

    query = ' '.join(sys.argv[1:])

    # Determine repo root - support two scenarios:
    # 1. Tool in autonomous-issue-agent/tools/ → repo is ../repo/
    # 2. Tool in Connect-A-PIC-Pro/tools/ → repo is ../

    tool_dir = Path(__file__).parent
    parent_dir = tool_dir.parent

    # First check if parent directory looks like the actual project (has .sln or .csproj)
    has_solution = list(parent_dir.glob("*.sln"))
    has_project = (parent_dir / "Connect-A-Pic-Core").exists()

    if has_solution or has_project:
        # We're directly in the project! (tools/ is inside Connect-A-PIC-Pro/)
        repo_root = parent_dir
    # Otherwise check if we're in autonomous-issue-agent setup (has separate repo/ directory)
    elif (parent_dir / "repo").exists():
        repo_root = parent_dir / "repo"
    # Fallback: use current working directory
    else:
        repo_root = Path.cwd()

    # Resolve to absolute path (handles ../repo correctly)
    repo_root = repo_root.resolve()

    if not repo_root.exists():
        print(f"ERROR: Repository not found at {repo_root}", file=sys.stderr)
        print(f"       Tool location: {tool_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"📁 Repository: {repo_root}", file=sys.stderr)

    # Build or load index
    force_rebuild = '--rebuild' in sys.argv
    index = build_index(repo_root, force_rebuild=force_rebuild)

    # Search
    print(f"\nSearching for: {query}\n", file=sys.stderr)
    results = search(query, index)

    # Output results (parseable format for agent)
    print("## Relevant Files:")
    for file_path, score, lines in results:
        # Make path relative to repo root
        rel_path = Path(file_path).relative_to(repo_root)
        print(f"- {rel_path} (score: {score:.3f}, lines: {lines})")

    # Also output detailed results to stderr for debugging
    print("\n## Details:", file=sys.stderr)
    for file_path, score, lines in results:
        rel_path = Path(file_path).relative_to(repo_root)
        print(f"\n{rel_path} (similarity: {score:.3f})", file=sys.stderr)
        print(f"  Lines: {lines}", file=sys.stderr)


if __name__ == '__main__':
    main()
