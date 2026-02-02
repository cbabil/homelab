# Contributing

Thank you for your interest in contributing to Tomo!

---

## Ways to Contribute

### Bug Reports

Found a bug? Help us fix it:

1. Check [existing issues](https://github.com/cbabil/tomo/issues) first
2. Use the bug report template
3. Include:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details
   - Relevant logs

### Feature Requests

Have an idea? We'd love to hear it:

1. Check existing feature requests
2. Use the feature request template
3. Describe the use case
4. Explain the expected behavior

### Documentation

Help improve our docs:

- Fix typos and errors
- Add examples
- Improve clarity
- Translate content

### Code Contributions

Want to contribute code? Read on!

---

## Development Setup

See [[Development]] for complete setup instructions.

Quick start:
```bash
git clone https://github.com/cbabil/tomo.git
cd tomo
make setup
```

---

## Coding Standards

### Python (Backend)

- Follow [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- Use type hints everywhere
- Use Pydantic for data validation
- Maximum line length: 88 characters (Black default)
- Maximum file length: 120 lines (prefer smaller)

**Example:**
```python
from typing import Optional
from pydantic import BaseModel

class ServerCreate(BaseModel):
    """Schema for creating a server."""

    name: str
    hostname: str
    port: int = 22
    username: str
    password: Optional[str] = None
```

### TypeScript (Frontend/CLI)

- Use TypeScript strict mode
- Use functional components with hooks
- Use Zod for runtime validation
- Maximum line length: 100 characters
- Maximum file length: 120 lines

**Example:**
```typescript
interface ServerProps {
  server: Server;
  onEdit: (id: number) => void;
}

export function ServerCard({ server, onEdit }: ServerProps) {
  return (
    <div className="card">
      <h3>{server.name}</h3>
      <Button onClick={() => onEdit(server.id)}>Edit</Button>
    </div>
  );
}
```

---

## Git Workflow

### Branch Naming

```
feature/short-description
fix/issue-number-description
docs/what-you-changed
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting (no code change)
- `refactor` - Code refactoring
- `test` - Adding tests
- `chore` - Maintenance

**Examples:**
```
feat(auth): add password reset flow
fix(servers): handle offline status correctly
docs(readme): update installation steps
```

---

## Pull Request Process

### Before Submitting

1. **Create a branch** from `dev`:
   ```bash
   git checkout dev
   git pull
   git checkout -b feature/my-feature
   ```

2. **Make your changes** following coding standards

3. **Run quality checks**:
   ```bash
   make lint
   make format
   make typecheck
   make test
   ```

4. **Commit your changes** with conventional commits

5. **Push your branch**:
   ```bash
   git push origin feature/my-feature
   ```

### Creating the PR

1. Go to GitHub and create a Pull Request
2. Target the `dev` branch
3. Fill out the PR template
4. Link any related issues

### PR Requirements

- [ ] All tests pass
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Documentation updated (if needed)
- [ ] Follows coding standards
- [ ] Descriptive commit messages

### Review Process

1. Maintainers will review your PR
2. Address any feedback
3. Once approved, it will be merged

---

## Testing

### Writing Tests

**Backend:**
```python
import pytest
from src.services.server_service import ServerService

class TestServerService:
    def test_create_server(self):
        service = ServerService()
        server = service.create(name="Test", hostname="1.2.3.4")
        assert server.name == "Test"
```

**Frontend:**
```typescript
import { render, screen } from '@testing-library/react';
import { ServerCard } from './ServerCard';

test('displays server name', () => {
  render(<ServerCard server={mockServer} onEdit={() => {}} />);
  expect(screen.getByText('Production')).toBeInTheDocument();
});
```

### Running Tests

```bash
# All tests
make test

# Backend only
make test-backend

# Frontend only
make test-frontend
```

---

## Project Structure

When adding new features, follow these patterns:

### Backend Feature

```
backend/src/
├── tools/
│   └── myfeature/
│       ├── __init__.py
│       └── tools.py          # MCP tools
├── services/
│   └── myfeature_service.py  # Business logic
└── models/
    └── myfeature.py          # Data models
```

### Frontend Feature

```
frontend/src/
├── pages/
│   └── myfeature/
│       ├── MyFeaturePage.tsx
│       └── index.ts
├── components/
│   └── myfeature/
│       ├── MyComponent.tsx
│       └── index.ts
└── hooks/
    └── useMyFeature.ts
```

---

## Issue Labels

| Label | Description |
|-------|-------------|
| `bug` | Something isn't working |
| `enhancement` | New feature request |
| `documentation` | Documentation improvement |
| `good first issue` | Good for newcomers |
| `help wanted` | Extra attention needed |
| `priority: high` | High priority |
| `wontfix` | Won't be addressed |

---

## Code Review Guidelines

### For Reviewers

- Be constructive and respectful
- Explain the "why" behind suggestions
- Approve when requirements are met
- Test locally when needed

### For Contributors

- Respond to feedback promptly
- Ask questions if unclear
- Update PR based on feedback
- Thank reviewers for their time

---

## Getting Help

- **Questions?** Open a discussion on GitHub
- **Stuck?** Ask in the issue/PR
- **Need guidance?** Look for `good first issue` labels

---

## Recognition

Contributors are recognized in:
- Release notes
- Contributors file
- Our eternal gratitude!

---

## Code of Conduct

Be respectful and inclusive. We're all here to build something great together.

---

## License

By contributing, you agree that your contributions will be licensed under the project's license. See [LICENSE](https://github.com/cbabil/tomo/blob/main/LICENSE) for details.
