# Contributing to SuperAI

We welcome contributions to the SuperAI project! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a new branch for your changes
5. Make your changes
6. Test your changes
7. Submit a pull request

## Development Setup

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Python 3.11+
- Git

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/SuperAI.git
   cd SuperAI
   ```

2. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

3. Start the development environment:
   ```bash
   docker-compose up -d
   ```

4. Verify all services are running:
   ```bash
   docker-compose ps
   ```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-agent-type`
- `bugfix/fix-event-bus-memory-leak`
- `docs/update-installation-guide`
- `refactor/improve-error-handling`

### Commit Messages

Follow conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(agent-planner): add retry mechanism for failed tasks

fix(event-bus): resolve gevent compatibility issues

docs(readme): update installation instructions
```

## Submitting Changes

### Pull Request Process

1. Ensure your code follows the coding standards
2. Add or update tests as needed
3. Update documentation if required
4. Ensure all tests pass
5. Create a pull request with:
   - Clear title and description
   - Reference to related issues
   - Screenshots if UI changes
   - Testing instructions

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes
```

## Coding Standards

### Python Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use meaningful variable and function names
- Add docstrings for classes and functions

### Docker Best Practices

- Use multi-stage builds when appropriate
- Minimize layer count
- Use specific base image tags
- Follow security best practices
- Add health checks

### Configuration

- Use environment variables for configuration
- Provide sensible defaults
- Document all configuration options
- Use configuration validation

## Testing

### Running Tests

```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests
python -m pytest tests/integration/

# Run all tests with coverage
python -m pytest --cov=core --cov=microservices
```

### Test Guidelines

- Write tests for new features
- Maintain test coverage above 80%
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies

### Test Structure

```
tests/
├── unit/
│   ├── core/
│   └── microservices/
├── integration/
│   ├── test_event_bus.py
│   └── test_agent_communication.py
└── fixtures/
    └── sample_data.py
```

## Documentation

### Documentation Types

- **README.md**: Project overview and quick start
- **User Manual**: Detailed usage instructions
- **API Documentation**: Service endpoints and schemas
- **Architecture Documentation**: System design and components
- **Troubleshooting**: Common issues and solutions

### Documentation Standards

- Use clear, concise language
- Include code examples
- Add screenshots for UI features
- Keep documentation up-to-date
- Use proper markdown formatting

### Building Documentation

```bash
# Generate API documentation
python scripts/generate_docs.py

# Validate documentation links
python scripts/validate_docs.py
```

## Issue Reporting

### Bug Reports

Include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Log files or error messages
- Screenshots if applicable

### Feature Requests

Include:
- Clear description of the feature
- Use case and motivation
- Proposed implementation approach
- Potential impact on existing features

## Community

### Getting Help

- Check existing documentation
- Search existing issues
- Join community discussions
- Ask questions in issues

### Communication Channels

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: General questions and ideas
- Pull Requests: Code review and collaboration

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to SuperAI! 🚀