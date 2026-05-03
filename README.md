# CodeBaseChat

AI-powered conversational interface for exploring and understanding codebases.

## Overview

CodeBaseChat lets you chat with your codebase. Ask questions in natural language, get answers grounded in your actual source files, and navigate large projects without endless grepping or clicking through directories.

## Features

- **Natural language queries** — Ask "how does auth work?" instead of searching for files.
- **Context-aware answers** — Responses reference actual functions, classes, and file paths.
- **Multi-repo support** — Index and switch between multiple projects seamlessly.
- **Incremental indexing** — Only re-index files that changed since the last scan.
- **Privacy-first** — Local embeddings and LLM options; no code leaves your machine unless you choose.

## Getting Started

### Prerequisites

- Python 3.10+
- Git

### Installation

```bash
git clone https://github.com/BlackWh1te/CodeBaseChat.git
cd CodeBaseChat
pip install -r requirements.txt
```

### Quick Start

```bash
# Index your project
python -m codebasechat index ./my-project

# Start chatting
python -m codebasechat chat
```

## Usage

### Indexing a repository

```bash
python -m codebasechat index /path/to/repo --name my-project
```

### Asking questions

```bash
python -m codebasechat query "How is the database connection handled?"
```

### Starting the interactive shell

```bash
python -m codebasechat shell
```

## Roadmap

- [ ] VS Code extension
- [ ] Web UI with real-time collaboration
- [ ] Support for more embedding providers (OpenAI, Cohere, local)
- [ ] Git diff-aware Q&A

## Contributing

Contributions are welcome! Please open an issue or pull request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-thing`)
3. Commit your changes (`git commit -m 'Add amazing thing'`)
4. Push to the branch (`git push origin feat/amazing-thing`)
5. Open a Pull Request

## License

MIT License. See [LICENSE](LICENSE) for details.

---

Built with care by [BlackWh1te](https://github.com/BlackWh1te).
