# BRD Agent Framework - Test Suite

## Running Tests

### Install Test Dependencies
```powershell
pip install -r tests/requirements-test.txt
```

### Run All Tests
```powershell
pytest tests/ -v
```

### Run Specific Test Suite
```powershell
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v
```

### Run with Coverage
```powershell
pytest tests/ --cov=tools --cov=config --cov-report=html

# View coverage report
Start-Process htmlcov/index.html
```

## Test Structure

```
tests/
├── unit/                       # Fast, isolated tests
│   ├── test_gitpython_adapter.py    # Adapter tests
│   ├── test_config_loader.py        # Config tests (TODO)
│   └── test_tool_factory.py         # Factory tests (TODO)
├── integration/                # Full pipeline tests
│   └── test_full_pipeline.py        # End-to-end tests
├── fixtures/                   # Test data
│   ├── sample_java_repo/
│   ├── sample_typescript_repo/
│   └── expected_outputs/
└── requirements-test.txt       # Test dependencies
```

## Writing Tests

### Unit Test Template
```python
import pytest
from your_module import YourClass

@pytest.fixture
def sample_config():
    return {"key": "value"}

def test_feature(sample_config):
    obj = YourClass(sample_config)
    result = obj.method()
    assert result == expected_value
```

### Integration Test Template
```python
def test_pipeline_scenario(tmp_path):
    # Setup test repository
    repo = setup_test_repo(tmp_path)
    
    # Run pipeline
    result = run_pipeline(repo)
    
    # Verify outputs
    assert result['success'] == True
    assert (repo / "KB" / "artifacts").exists()
```

## Test Coverage Goals

| Component | Target Coverage |
|-----------|----------------|
| Adapters | 90% |
| Config | 85% |
| Core Logic | 80% |
| Overall | 80% |

## Continuous Integration

```yaml
# .github/workflows/tests.yml (TODO)
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install -r tests/requirements-test.txt
      - run: pytest tests/ --cov --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Current Status

✅ **Implemented:**
- Unit tests for `GitPythonAdapter`
- Test structure and fixtures
- Coverage configuration

⚠️ **TODO:**
- Unit tests for other adapters
- Integration tests for full pipeline
- Golden file validation
- CI/CD integration
- Performance benchmarks

## Running Tests Against Real Repos

```powershell
# Test on docusaurus
pytest tests/integration/ --repo-path="./docusaurus" -v

# Test on jpetstore-6
pytest tests/integration/ --repo-path="./jpetstore-6" -v
```

*Last Updated: August 12, 2026*
