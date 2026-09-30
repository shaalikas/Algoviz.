import json
from pathlib import Path

from ai.analyzer import AIAnalyzer


def main() -> None:
    sample_path = Path(__file__).parent / "sample_data" / "sample_metadata.json"
    metadata = json.loads(sample_path.read_text(encoding="utf-8"))

    result = AIAnalyzer().analyze(metadata)

    print("=" * 72)
    print(f"AlgoViz AI Engine — source: {result['source']}")
    print("=" * 72)
    if result.get("error"):
        print(f"API fallback reason: {result['error']}")
        print()
    print(result["explanation"])


if __name__ == "__main__":
    main()
