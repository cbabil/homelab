# Testing Strategy & Guidelines

This document outlines the comprehensive testing strategy for the Tomo project, ensuring code quality and preventing regressions through systematic testing approaches.

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Types](#test-types)
- [Backend Testing (Python)](#backend-testing-python)
- [Frontend Testing (React/TypeScript)](#frontend-testing-reacttypescript)
- [Running Tests](#running-tests)
- [Coverage Requirements](#coverage-requirements)
- [Test-Driven Development](#test-driven-development)
- [Security Testing](#security-testing)
- [CI/CD Integration](#cicd-integration)

## Testing Philosophy

Our testing strategy follows these core principles:

- **Test Behavior, Not Implementation**: Focus on what the code does, not how it does it
- **100-Line Rule Compliance**: All test files follow the mandatory 100-line limit per file/function
- **Red-Green-Refactor**: TDD cycle with failing tests first, minimal code to pass, then refactor
- **Comprehensive Coverage**: Unit, integration, and end-to-end testing for complete validation
- **Security-First**: Dedicated security testing for SSH connections and encryption

## Test Types

### Unit Tests
- Test individual functions and classes in isolation
- Mock external dependencies
- Fast execution (< 100ms per test)
- 90% code coverage requirement

### Integration Tests
- Test component interactions and service integration
- Real database connections and API calls where appropriate
- Validate MCP protocol compliance
- Test error handling and recovery

### End-to-End Tests
- Full user workflows from frontend to backend
- Real browser automation where applicable
- Network communication testing
- Performance validation

## Backend Testing (Python)

### Framework: pytest + pytest-asyncio
- **Location**: `backend/tests/`
- **Configuration**: `backend/pyproject.toml`
- **Fixtures**: `backend/tests/conftest.py`

### Test Structure
```
backend/tests/
├── unit/           # Unit tests for individual modules
├── integration/    # Service integration tests
├── fixtures/       # Test data and factories
└── conftest.py     # Shared pytest configuration
```

### Key Testing Areas
- **SSH Service**: Paramiko mocking, connection handling, error scenarios
- **MCP Tools**: Health checks, tool registration, protocol compliance
- **Encryption**: Credential encryption/decryption, key derivation
- **Data Models**: Pydantic validation, field constraints, error handling

### Running Backend Tests
```bash
# All tests
make test-backend

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Security tests
pytest -m security -v

# With coverage
pytest --cov=src --cov-report=html
```

## Frontend Testing (React/TypeScript)

### Framework: Vitest + React Testing Library
- **Location**: `frontend/src/test/`
- **Configuration**: `frontend/vitest.config.ts`
- **Setup**: `frontend/src/test/setup.ts`

### Test Structure
```
frontend/src/
├── components/
│   └── layout/
│       ├── Header.test.tsx
│       └── Navigation.test.tsx
├── services/
│   └── mcpClient.test.ts
├── providers/
│   └── MCPProvider.test.tsx
└── test/
    ├── integration/     # Integration tests
    ├── mocks/          # MSW mock handlers
    └── setup.ts        # Test configuration
```

### Key Testing Areas
- **MCP Client**: Connection management, tool calling, error handling
- **React Components**: Rendering, user interactions, accessibility
- **Context Providers**: State management, error boundaries
- **Integration**: Frontend-backend communication, protocol compliance

### Running Frontend Tests
```bash
# All tests
make test-frontend

# Watch mode
npm run test:watch

# With coverage
npm run test:coverage

# UI mode
npm run test:ui
```

## Running Tests

### Quick Commands
```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test types
make test-unit
make test-integration

# CI environment
make ci-test
```

### Individual Test Commands
```bash
# Backend specific
cd backend && python -m pytest tests/unit/test_ssh_service.py -v

# Frontend specific
cd frontend && npm run test -- Header.test.tsx

# Run single test function
cd backend && python -m pytest tests/unit/test_encryption.py::TestCredentialManager::test_encrypt_decrypt_cycle -v
```

## Coverage Requirements

### Minimum Coverage Thresholds
- **Overall**: 90% line coverage
- **Backend**: 90% line coverage, 85% branch coverage
- **Frontend**: 80% line coverage, 75% branch coverage

### Coverage Reports
- **Backend**: HTML report in `backend/htmlcov/`
- **Frontend**: HTML report in `frontend/coverage/`
- **Combined**: Aggregated in `coverage/`

### Exclusions
- Test files themselves
- Configuration files
- Generated code
- Type definition files

## Test-Driven Development

### Red-Green-Refactor Cycle
1. **Red**: Write failing test that describes desired behavior
2. **Green**: Write minimal code to make test pass
3. **Refactor**: Improve code while keeping tests green

### Example TDD Workflow
```python
# 1. Red - Write failing test
def test_ssh_connection_success(self, ssh_service):
    result = await ssh_service.test_connection("host", 22, "user", "password", {})
    assert result[0] is True  # This will fail initially

# 2. Green - Implement minimal functionality
async def test_connection(self, host, port, username, auth_type, credentials):
    return True, "Connection successful", {}  # Minimal implementation

# 3. Refactor - Add proper implementation while keeping test green
```

## Security Testing

### Security Test Markers
Tests related to security are marked with `@pytest.mark.security`:

```python
@pytest.mark.security
def test_credential_encryption_strength():
    # Test encryption strength and key derivation
    pass

@pytest.mark.security 
def test_ssh_connection_security():
    # Test SSH security configurations
    pass
```

### Security Testing Areas
- **Credential Encryption**: AES-256 encryption, key derivation (PBKDF2)
- **SSH Security**: Host key validation, secure transport settings
- **Input Validation**: SQL injection, command injection prevention
- **Authentication**: Token validation, session management

## CI/CD Integration

### GitHub Actions Workflow
- **Location**: `.github/workflows/test.yml`
- **Triggers**: Push to main/develop, pull requests
- **Matrix Testing**: Multiple Python/Node versions

### Pipeline Stages
1. **Lint**: Code style and format checking
2. **Type Check**: Static type validation
3. **Unit Tests**: Fast isolated tests
4. **Integration Tests**: Service interaction tests
5. **Security Tests**: Security-focused validation
6. **Coverage**: Coverage reporting and enforcement

### Quality Gates
- All tests must pass
- Coverage thresholds must be met
- Linting must pass without warnings
- Type checking must pass without errors

## Best Practices

### Test Organization
- One test file per source file
- Group related tests in classes
- Use descriptive test names that explain behavior
- Follow AAA pattern (Arrange, Act, Assert)

### Mocking Guidelines
- Mock external dependencies (databases, APIs, file system)
- Don't mock the code under test
- Use realistic mock data
- Reset mocks between tests

### Test Data
- Use factories for complex test data
- Avoid hardcoded values where possible
- Create reusable fixtures
- Clean up test data after tests

### Performance
- Keep unit tests under 100ms
- Use parallel test execution where possible
- Mock expensive operations
- Profile slow tests and optimize

## Troubleshooting

### Common Issues
- **Import Errors**: Check PYTHONPATH and module imports
- **Async Test Issues**: Ensure proper async/await usage
- **Mock Problems**: Verify mock patches and reset calls
- **Coverage Issues**: Check exclusion patterns and test execution

### Debug Commands
```bash
# Run tests with debug output
pytest -v -s tests/unit/test_ssh_service.py

# Run with pdb on failures
pytest --pdb tests/unit/test_encryption.py

# Check coverage details
pytest --cov=src --cov-report=term-missing
```

This testing strategy ensures comprehensive validation of the Tomo project while maintaining code quality and preventing regressions.