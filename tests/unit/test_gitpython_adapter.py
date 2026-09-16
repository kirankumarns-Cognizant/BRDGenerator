"""
Unit tests for GitPythonAdapter
"""

import pytest
from pathlib import Path
from tools.adapters.gitpython_adapter import GitPythonAdapter


@pytest.fixture
def config():
    """Sample configuration for testing."""
    return {
        'supported_languages': {
            'java': {
                'source_extensions': ['.java'],
                'config_extensions': ['.xml', '.properties'],
                'framework_indicators': ['pom.xml', 'build.gradle'],
                'test_patterns': ['**/test/**', '**/*Test.java']
            },
            'typescript': {
                'source_extensions': ['.ts', '.tsx', '.js'],
                'config_extensions': ['.json', '.yaml'],
                'framework_indicators': ['package.json', 'tsconfig.json'],
                'test_patterns': ['**/__tests__/**', '**/*.test.*']
            },
            'python': {
                'source_extensions': ['.py'],
                'config_extensions': ['.yaml', '.toml'],
                'framework_indicators': ['requirements.txt', 'setup.py'],
                'test_patterns': ['**/tests/**', '**/test_*.py']
            }
        },
        'adapter_retry': {
            'max_attempts': 3,
            'backoff_multiplier': 2,
            'initial_delay_seconds': 0.1,
            'max_delay_seconds': 1
        }
    }


@pytest.fixture
def adapter(config):
    """Create adapter instance."""
    return GitPythonAdapter(config)


def test_adapter_initialization(adapter):
    """Test adapter initializes with config."""
    assert adapter.config is not None
    assert len(adapter.all_source_extensions) > 0
    assert adapter.max_attempts == 3


def test_detect_java_language(adapter, tmp_path):
    """Test Java language detection."""
    # Create sample Java files
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "Main.java").write_text("public class Main {}")
    (tmp_path / "pom.xml").write_text("<project></project>")
    
    result = adapter.scan_repo(str(tmp_path))
    
    assert result['primary_language'] == 'java'
    assert 'java' in result['detected_languages']
    assert len(result['source_files']) == 1
    assert len(result['framework_indicators']) == 1
    assert result['confidence'] > 0.7


def test_detect_typescript_language(adapter, tmp_path):
    """Test TypeScript language detection."""
    # Create sample TypeScript files
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.ts").write_text("const x: number = 5;")
    (tmp_path / "package.json").write_text('{"name": "test"}')
    (tmp_path / "tsconfig.json").write_text('{}')
    
    result = adapter.scan_repo(str(tmp_path))
    
    assert result['primary_language'] == 'typescript'
    assert 'typescript' in result['detected_languages']
    assert len(result['source_files']) == 1
    assert len(result['framework_indicators']) == 2


def test_detect_python_language(adapter, tmp_path):
    """Test Python language detection."""
    # Create sample Python files
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def hello(): pass")
    (tmp_path / "requirements.txt").write_text("requests==2.28.0")
    
    result = adapter.scan_repo(str(tmp_path))
    
    assert result['primary_language'] == 'python'
    assert 'python' in result['detected_languages']
    assert len(result['source_files']) == 1
    assert len(result['framework_indicators']) == 1


def test_test_file_detection(adapter, tmp_path):
    """Test test file pattern matching."""
    # Create test files
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("def test_foo(): pass")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MainTest.java").write_text("public class MainTest {}")
    
    result = adapter.scan_repo(str(tmp_path))
    
    assert len(result['test_files']) == 2
    assert any('test_main.py' in f for f in result['test_files'])
    assert any('MainTest.java' in f for f in result['test_files'])


def test_skip_directories(adapter, tmp_path):
    """Test that skip directories are ignored."""
    # Create files in skip directories
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lib.js").write_text("// library")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("config")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.js").write_text("const x = 1;")
    
    result = adapter.scan_repo(str(tmp_path))
    
    # Should only find app.js, not files in node_modules or .git
    assert len(result['source_files']) == 1
    assert 'app.js' in result['source_files'][0]


def test_nonexistent_repo(adapter):
    """Test handling of nonexistent repository."""
    result = adapter.scan_repo("/path/that/does/not/exist")
    
    assert result['total_files'] == 0
    assert result['confidence'] == 0.0
    assert 'error' in result


def test_unsafe_path_detection(adapter):
    """Test security validation of paths."""
    unsafe_paths = [
        "../../../etc/passwd",
        "~/malicious",
        "/tmp/../../../etc"
    ]
    
    for path in unsafe_paths:
        result = adapter.scan_repo(path)
        assert result['confidence'] <= 0.3  # Should fail with low confidence


def test_multi_language_repo(adapter, tmp_path):
    """Test repository with multiple languages."""
    # Create files in multiple languages
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "server.py").write_text("from flask import Flask")
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "app.ts").write_text("const app = {};")
    (tmp_path / "package.json").write_text('{}')
    (tmp_path / "requirements.txt").write_text("flask")
    
    result = adapter.scan_repo(str(tmp_path))
    
    assert len(result['detected_languages']) == 2
    assert 'python' in result['detected_languages']
    assert 'typescript' in result['detected_languages']
    assert len(result['source_files']) == 2


def test_confidence_scoring(adapter, tmp_path):
    """Test confidence scoring based on findings."""
    # High confidence: source files + framework indicators
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "Main.java").write_text("public class Main {}")
    (tmp_path / "pom.xml").write_text("<project></project>")
    
    result = adapter.scan_repo(str(tmp_path))
    assert result['confidence'] >= 0.8
    
    # Lower confidence: no framework indicators
    tmp_path2 = tmp_path / "test2"
    tmp_path2.mkdir()
    (tmp_path2 / "script.py").write_text("print('hello')")
    
    result2 = adapter.scan_repo(str(tmp_path2))
    assert result2['confidence'] < 0.8


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
