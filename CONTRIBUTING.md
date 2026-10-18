# Contributing to CodeSense

Thank you for your interest in contributing to **CodeSense**! We welcome contributions from developers, educators, and learners alike.

---

## Code of Conduct

All contributors and participants are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md). Please treat everyone with respect and empathy.

---

## How Can I Contribute?

1. **Reporting Bugs**: Check the [Issues tab](https://github.com/your-username/CodeSense/issues) to ensure the bug hasn't already been reported. Use the Bug Report issue template.
2. **Suggesting Enhancements**: Propose new error categories, static analysis rules, or UI features using the Feature Request template.
3. **Submitting Pull Requests**: Follow the development guidelines below.

---

## Development Workflow

### 1. Prerequisites
- **Git**
- **Python 3.12+**
- **Node.js 20+** and `npm`
- **OpenJDK 17+** (Ensure `javac` is accessible on your system PATH)

### 2. Fork and Clone
```bash
git clone https://github.com/<your-username>/CodeSense.git
cd CodeSense
```

### 3. Backend Setup
```bash
cd backend
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python -m pytest
```

### 4. Frontend Setup
```bash
cd ../frontend
npm install
npm run build
npm run dev
```

---

## Pull Request Guidelines

1. **Create a branch**: Use descriptive branch names like `fix/type-error-message` or `feat/new-static-rule`.
2. **Run tests**: All automated tests must pass before opening a PR:
   ```bash
   cd backend
   python -m pytest
   cd ../frontend
   npm run build
   ```
3. **Preserve Compiler Truth**: The Java compiler (`javac`) is always the ground truth. Never bypass real compilation for synthetic predictions.
4. **Deterministic Fixes**: Automatic fixes must preserve the user's original program, modify only the necessary region, and be validated via compiler recompilation.
5. **Clean Commits**: Write clear, concise commit messages following conventional commit format (`feat:`, `fix:`, `docs:`, `test:`).

---

## Reporting Security Issues

Please review our [Security Policy](SECURITY.md) for instructions on securely reporting vulnerabilities.
