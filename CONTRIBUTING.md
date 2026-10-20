# Contributing to StudyGuard

Thank you for your interest in contributing to StudyGuard!

## Development Workflow

1. Fork the repository and clone your fork.
2. Create a virtual environment and install dev dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```
3. Create a feature branch from `main`.
4. Make your changes following the coding standards in `docs/CODING_STANDARDS.md`.
5. Write or update tests as needed. All tests must pass:
   ```bash
   pytest tests/ -v
   ```
6. Update documentation if applicable.
7. Submit a pull request to `main`.

## Coding Standards

All contributions must follow the conventions defined in [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md):

- Google-style docstrings for all public functions and classes
- Type annotations on all public function parameters and return values
- `snake_case` for modules, functions, and variables
- `PascalCase` for classes
- `pathlib.Path` for all file paths
- `time.monotonic()` for all timing operations
- No hardcoded absolute paths
- No magic numbers — use configuration values

## Interface Specifications

New modules must conform to the interface patterns defined in [docs/INTERFACE_SPEC.md](docs/INTERFACE_SPEC.md). If you need to add a new module, propose the interface first.

## Testing Requirements

- All tests must run without a real camera
- Use synthetic data, mock objects, or generated video frames
- Timer-dependent tests must use injectable clocks
- One logical assertion per test when possible
- Test file naming: `test_<module>.py`

## Pull Request Checklist

- [ ] Code follows `docs/CODING_STANDARDS.md`
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] No camera-dependent tests
- [ ] Documentation updated if needed
- [ ] No sensitive data, credentials, or personal information included
- [ ] Commit messages are clear and descriptive

## Troubleshooting

### Running pytest in a ROS 2 environment

If your shell has ROS 2 sourced (for example `source /opt/ros/jazzy/setup.bash`
sets `PYTHONPATH`), pytest may try to auto-load the ROS 2 pytest plugins and fail
with `ModuleNotFoundError: No module named 'yaml'`. Run pytest with plugin autoload
disabled:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/ -v
```

This is an environment-only workaround and does not change any project configuration.

## Reporting Issues

When reporting bugs, please include:

1. Python version and OS
2. Steps to reproduce
3. Expected vs actual behavior
4. Error messages (full traceback)
5. Configuration file contents (if relevant)

## Architecture Decisions

Significant changes to architecture, technology choices, or module interfaces require an Architecture Decision Record (ADR) in `docs/DECISIONS.md`. Propose the ADR before implementing the change.
