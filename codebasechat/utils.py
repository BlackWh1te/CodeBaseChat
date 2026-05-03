"""Utility helpers."""

import os
import re
from pathlib import Path


def parse_gitignore(root: Path) -> list[str]:
    """Read .gitignore and return list of patterns."""
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return []
    patterns = []
    with gitignore.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


def match_gitignore(rel_path: str, patterns: list[str]) -> bool:
    """Very simple .gitignore matcher."""
    for pat in patterns:
        if pat.startswith("/"):
            if rel_path.startswith(pat[1:]) or rel_path == pat[1:]:
                return True
        elif pat.endswith("/"):
            if f"/{pat[:-1]}/" in f"/{rel_path}/" or rel_path.startswith(pat):
                return True
        else:
            if pat in rel_path or rel_path.endswith(f"/{pat}") or rel_path == pat:
                return True
    return False


def should_index(path: Path, root: Path, gitignore_patterns: list[str]) -> bool:
    """Decide if a file should be indexed."""
    rel = path.relative_to(root).as_posix()

    # Skip hidden directories/files
    if any(part.startswith(".") for part in path.relative_to(root).parts):
        return False

    if match_gitignore(rel, gitignore_patterns):
        return False

    # Only index text code-ish files
    text_exts = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp",
        ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala",
        ".html", ".css", ".scss", ".sass", ".less",
        ".sql", ".sh", ".bash", ".zsh", ".fish",
        ".md", ".txt", ".json", ".yaml", ".yml", ".xml", ".toml",
        ".dockerfile", ".makefile", ".cmake", ".gradle",
    }
    if path.suffix.lower() in text_exts or path.name.lower() in {
        "dockerfile", "makefile", "cmakelists.txt", "gemfile", "rakefile",
    }:
        return True
    return False


def walk_repo(root: Path) -> list[Path]:
    """Yield files under root that should be indexed."""
    gitignore_patterns = parse_gitignore(root)
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune hidden directories
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".")
            and not match_gitignore(
                Path(dirpath).relative_to(root).as_posix() + "/" + d,
                gitignore_patterns,
            )
        ]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            if should_index(fpath, root, gitignore_patterns):
                files.append(fpath)
    return sorted(files)
