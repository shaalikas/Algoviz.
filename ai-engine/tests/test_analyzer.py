import json
from unittest.mock import Mock, patch

from ai.analyzer import AIAnalyzer


def sample():
    return {
        "repository": {"name": "demo", "language": "Python", "description": "Demo API"},
        "files": [
            {
                "path": "app.py",
                "language": "Python",
                "imports": ["flask"],
                "classes": ["App"],
                "functions": ["main"],
                "unnecessary_field": "should be removed",
            }
        ],
        "dependencies": ["flask"],
        "architecture": {"layers": ["API", "Service"], "ignored": "x"},
        "detected_risks": ["hardcoded config"],
        "circular_dependencies": [],
    }


def test_compact_metadata():
    result = AIAnalyzer.compact_metadata(sample())
    assert "unnecessary_field" not in result["files"][0]
    assert result["files"][0]["path"] == "app.py"
    assert result["architecture"] == {"layers": ["API", "Service"]}
    assert result["dependencies"] == ["flask"]


def test_missing_fields_are_handled():
    result = AIAnalyzer(api_key=None).analyze({"repository": {"name": "tiny"}})
    assert result["source"] == "local fallback"
    assert "No dependencies were supplied." in result["explanation"]


@patch("ai.analyzer.requests.post")
def test_api_response_parsing(mock_post):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "choices": [{"message": {"content": "AI explanation"}}]
    }
    mock_post.return_value = response

    result = AIAnalyzer(api_key="test-key").analyze(sample())
    assert result["source"] == "AI API"
    assert result["explanation"] == "AI explanation"
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert mock_post.call_args.kwargs["json"]["model"] == "openai/gpt-oss-20b"


@patch("ai.analyzer.requests.post")
def test_api_failure_uses_fallback(mock_post):
    import requests
    mock_post.side_effect = requests.Timeout("timed out")

    result = AIAnalyzer(api_key="test-key").analyze(sample())
    assert result["source"] == "local fallback"
    assert "Repository overview" in result["explanation"]


@patch("ai.analyzer.requests.post")
def test_malformed_api_response_uses_fallback(mock_post):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"unexpected": "shape"}
    mock_post.return_value = response

    result = AIAnalyzer(api_key="test-key").analyze(sample())
    assert result["source"] == "local fallback"
