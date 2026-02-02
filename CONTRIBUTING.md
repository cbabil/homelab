# Contributing to Tomo

Thank you for your interest in contributing to Tomo! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## Getting Started

### Prerequisites

- Node.js 18+ (for frontend/CLI)
- Python 3.12+ (for backend)
- Yarn package manager
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/tomo.git
   cd tomo
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   yarn install
   ```

4. **Set up the CLI**
   ```bash
   cd cli
   yarn install
   ```

## Development Workflow

### Branch Naming

- `feat/<description>` - New features
- `fix/<description>` - Bug fixes
- `docs/<description>` - Documentation changes
- `refactor/<description>` - Code refactoring
- `test/<description>` - Test additions or changes

### Commit Messages

We follow conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or modifications
- `chore`: Maintenance tasks

Examples:
```
feat(servers): add SSH connection status indicator
fix(auth): resolve token refresh timing issue
docs(readme): update installation instructions
```

### Pull Requests

1. Create a feature branch from `dev`
2. Make your changes
3. Write or update tests as needed
4. Ensure all tests pass
5. Submit a PR to `dev` branch

#### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added/updated for changes
- [ ] Documentation updated if needed
- [ ] All tests passing
- [ ] No console.log or debug statements
- [ ] TypeScript types properly defined

## Testing

### Frontend Tests

```bash
cd frontend

# Run unit tests
yarn test

# Run tests in watch mode
yarn test --watch

# Run E2E tests
yarn test:e2e
```

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/unit/test_auth.py
```

### CLI Tests

```bash
cd cli
yarn test
```

## Code Style

### TypeScript/JavaScript

- Use TypeScript for all new code
- Follow ESLint configuration
- Use functional components with hooks in React
- Prefer named exports over default exports

### Python

- Follow PEP 8 style guide
- Use type hints
- Use async/await for I/O operations

### CSS

- Use Tailwind CSS utility classes
- Follow the design system tokens
- Mobile-first responsive design (when applicable)

## Project Structure

```
tomo/
├── backend/          # Python MCP server
│   ├── src/
│   │   ├── main.py
│   │   ├── services/
│   │   ├── tools/
│   │   └── models/
│   └── tests/
├── frontend/         # React application
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── providers/
│   └── tests/
├── cli/              # Command-line interface
│   └── src/
└── docs/             # Documentation
```

## Reporting Issues

When reporting bugs, please include:

1. Description of the issue
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. Environment details (OS, Node version, Python version)
6. Relevant logs or screenshots

## Feature Requests

For feature requests, please:

1. Check existing issues first
2. Describe the use case
3. Explain the expected behavior
4. Consider implementation complexity

## Questions?

If you have questions about contributing, please open a discussion or issue.

---

Thank you for contributing to Tomo!
