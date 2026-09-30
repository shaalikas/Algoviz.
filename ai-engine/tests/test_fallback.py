from ai.fallback import generate_fallback


def test_fallback_uses_metadata_only():
    metadata = {
        "repository": {"name": "Shop API", "language": "Python"},
        "files": [{"path": "app.py"}, {"path": "service.py"}],
        "dependencies": ["flask", "sqlalchemy"],
        "architecture": {"components": ["API", "Database"]},
        "detected_risks": [{"type": "cycle", "description": "A imports B"}],
        "circular_dependencies": [["a.py", "b.py", "a.py"]],
    }

    text = generate_fallback(metadata)

    assert "Shop API" in text
    assert "Python" in text
    assert "flask" in text
    assert "API, Database" in text
    assert "A imports B" in text
    assert "a.py -> b.py -> a.py" in text
    assert "made-up" not in text.lower()
