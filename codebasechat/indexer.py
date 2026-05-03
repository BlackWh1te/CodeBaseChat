"""Index a codebase into searchable chunks."""

import ast
import json
import hashlib
from pathlib import Path
from typing import Iterable

from codebasechat.utils import walk_repo


def chunk_file(path: Path, root: Path, max_chars: int = 1200) -> Iterable[dict]:
    """Yield chunks from a single file."""
    rel = path.relative_to(root).as_posix()
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return

    # If it's a Python file, try AST-based chunking
    if path.suffix == ".py" and len(text) < 500_000:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            tree = None
        if tree:
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    start = node.lineno
                    end = getattr(node, "end_lineno", start)
                    lines = text.splitlines()[start - 1:end]
                    chunk_text = "\n".join(lines)
                    if chunk_text.strip():
                        yield {
                            "file": rel,
                            "type": "class" if isinstance(node, ast.ClassDef) else "function",
                            "name": node.name,
                            "start_line": start,
                            "end_line": end,
                            "text": chunk_text,
                        }
            # Fallback: if no chunks produced, emit whole file
            # (some files are all module-level)

    # Greedy line chunking for everything else
    lines = text.splitlines()
    buffer = []
    start_line = 1
    for i, line in enumerate(lines, 1):
        buffer.append(line)
        chunk_text = "\n".join(buffer)
        if len(chunk_text) >= max_chars:
            yield {
                "file": rel,
                "type": "chunk",
                "name": "",
                "start_line": start_line,
                "end_line": i,
                "text": chunk_text,
            }
            buffer = []
            start_line = i + 1
    if buffer:
        yield {
            "file": rel,
            "type": "chunk",
            "name": "",
            "start_line": start_line,
            "end_line": len(lines),
            "text": "\n".join(buffer),
        }


def index_repo(repo_path: Path, index_dir: Path) -> Path:
    """Index a repository and save chunks to index_dir."""
    repo_path = repo_path.resolve()
    index_dir = index_dir.resolve()
    index_dir.mkdir(parents=True, exist_ok=True)

    chunks = []
    for fpath in walk_repo(repo_path):
        for chunk in chunk_file(fpath, repo_path):
            chunk["id"] = hashlib.md5(
                f"{chunk['file']}:{chunk['start_line']}:{chunk['text'][:200]}".encode()
            ).hexdigest()
            chunks.append(chunk)

    # Write index
    index_file = index_dir / f"{repo_path.name}.jsonl"
    with index_file.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    # Write manifest
    manifest = index_dir / "manifest.json"
    manifest_data = {}
    if manifest.exists():
        manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_data[repo_path.name] = str(index_file)
    manifest.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    return index_file
