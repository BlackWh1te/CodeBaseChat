"""CLI entry points for codebasechat."""

import argparse
import json
import os
import sys
from pathlib import Path

from codebasechat.indexer import index_repo
from codebasechat.search import SearchEngine


def get_index_dir() -> Path:
    return Path(os.environ.get("CODEBASECHAT_INDEX", Path.home() / ".codebasechat" / "index"))


def get_manifest() -> dict:
    idx = get_index_dir()
    manifest = idx / "manifest.json"
    if manifest.exists():
        return json.loads(manifest.read_text(encoding="utf-8"))
    return {}


def cmd_index(args):
    repo = Path(args.repo).resolve()
    if not repo.exists():
        print(f"error: path does not exist: {repo}", file=sys.stderr)
        sys.exit(1)
    idx_dir = get_index_dir()
    index_file = index_repo(repo, idx_dir)
    count = sum(1 for _ in index_file.open("r", encoding="utf-8"))
    print(f"Indexed {repo.name}: {count} chunks -> {index_file}")


def cmd_query(args):
    manifest = get_manifest()
    if not manifest:
        print("error: no indexes found. Run `codebasechat index <repo>` first.", file=sys.stderr)
        sys.exit(1)

    # Pick the most recently modified index if no name given
    target = args.name
    if not target:
        target = max(manifest, key=lambda k: Path(manifest[k]).stat().st_mtime)

    index_file = Path(manifest.get(target, target))
    if not index_file.exists():
        print(f"error: index not found for '{target}'", file=sys.stderr)
        sys.exit(1)

    engine = SearchEngine(index_file)
    results = engine.query(args.query, top_k=args.top_k)

    if not results:
        print("No results found.")
        return

    for r in results:
        loc = f"{r['file']}:{r['start_line']}"
        name_part = f" {r['name']}" if r.get('name') else ''
        header = f"[{r['score']}] {loc} ({r['type']}{name_part})"
        print(header)
        snippet = r["text"][:500].replace("\n", "\n  ")
        print(f"  {snippet}")
        print()


def cmd_shell(args):
    manifest = get_manifest()
    if not manifest:
        print("error: no indexes found. Run `codebasechat index <repo>` first.", file=sys.stderr)
        sys.exit(1)

    target = args.name
    if not target:
        target = max(manifest, key=lambda k: Path(manifest[k]).stat().st_mtime)

    index_file = Path(manifest.get(target, target))
    if not index_file.exists():
        print(f"error: index not found for '{target}'", file=sys.stderr)
        sys.exit(1)

    engine = SearchEngine(index_file)
    print(f"CodeBaseChat shell — querying '{target}'")
    print("Type 'quit' or 'exit' to leave.\n")

    while True:
        try:
            q = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if q.strip().lower() in {"quit", "exit", "q"}:
            break
        if not q.strip():
            continue
        results = engine.query(q, top_k=3)
        if not results:
            print("  (no results)")
            continue
        for r in results:
            loc = f"{r['file']}:{r['start_line']}"
            name_part = f" {r['name']}" if r.get('name') else ''
            header = f"[{r['score']}] {loc} ({r['type']}{name_part})"
            print(header)
            snippet = r["text"][:300].replace("\n", "\n  ")
            print(f"  {snippet}")
            print()


def main():
    parser = argparse.ArgumentParser(prog="codebasechat")
    sub = parser.add_subparsers(dest="cmd")

    p_index = sub.add_parser("index", help="index a repository")
    p_index.add_argument("repo", help="path to repository")
    p_index.set_defaults(func=cmd_index)

    p_query = sub.add_parser("query", help="query an indexed repository")
    p_query.add_argument("query", help="natural language query")
    p_query.add_argument("--name", "-n", default="", help="repository name (default: most recent)")
    p_query.add_argument("--top-k", "-k", type=int, default=5, help="number of results")
    p_query.set_defaults(func=cmd_query)

    p_shell = sub.add_parser("shell", help="interactive query shell")
    p_shell.add_argument("--name", "-n", default="", help="repository name (default: most recent)")
    p_shell.set_defaults(func=cmd_shell)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
