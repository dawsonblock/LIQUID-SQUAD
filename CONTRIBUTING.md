# Contributing to LIQUID HIVE 25

Thank you for considering contributing! This project is built for advanced research and production‑grade AI systems. Contributions must maintain clarity, modularity, and reproducibility.

## Workflow

1. **Fork + Branch**
   ```bash
   git clone <your-fork>
   git checkout -b feature/<short-name>
   ```

2. **Development Standards**
   - Python: type hints, docstrings, PEP8
   - Frontend: React + TypeScript, TailwindCSS
   - Write tests for new modules (`pytest` for Python, `jest` for frontend)
   - Keep functions small and composable

3. **Testing**
   ```bash
   pytest -q
   npm run test
   ```

4. **Commit Messages**
   - Format: `scope: change`
   - Example: `retrieval: add cross‑encoder reranker`

5. **Pull Requests**
   - Reference related issues
   - Include test results and docs updates
   - Keep PRs focused (1 feature/fix per PR)

## Coding Guidelines

- **Backend (Python)**: use FastAPI patterns (`routers`, `dependencies`).
- **Frontend (Next.js)**: favor function components + hooks.
- **CI/CD**: all tests must pass in GitHub Actions.
- **Docs**: update README, DEPLOYMENT, or ARCHITECTURE if you add/remove modules.

---

_Generated 2025-10-01T20:16:54.951056Z_
