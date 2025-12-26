from __future__ import annotations

import os

from utils.ai_analyzer import AIAnalyzer


def main() -> int:
    key = os.getenv("GEMINI_API_KEY") or os.getenv("AI_API_KEY") or ""
    print("HAS_KEY", bool(key))
    if not key:
        print("Defina GEMINI_API_KEY ou AI_API_KEY antes de testar.")
        return 2

    analyzer = AIAnalyzer(key, provider="gemini")
    ok, msg = analyzer.check_connection()
    print("OK", ok)
    print("MSG", msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
