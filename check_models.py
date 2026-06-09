"""List the Gemini models available to this API key and whether they support
generateContent. Run before run_benchmark.py to pick valid model IDs."""

import os
import json
from datetime import datetime

from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in .env")

client = genai.Client(api_key=API_KEY)

SKIP_KINDS = ("image", "tts", "audio", "embedding", "live", "robotics")


def strip_prefix(name):
    return name.split("/", 1)[1] if name and "/" in name else name


def main():
    os.makedirs("results", exist_ok=True)

    models = []
    for m in client.models.list():
        actions = list(getattr(m, "supported_actions", None) or [])
        models.append({
            "id": strip_prefix(m.name),
            "display_name": getattr(m, "display_name", "") or "",
            "supports_generate_content": "generateContent" in actions,
            "supported_actions": actions,
            "input_token_limit": getattr(m, "input_token_limit", None),
            "output_token_limit": getattr(m, "output_token_limit", None),
        })

    models.sort(key=lambda x: (not x["supports_generate_content"], x["id"]))
    usable = [m for m in models if m["supports_generate_content"]]

    print(f"{len(models)} models visible, {len(usable)} support generateContent\n")
    print(f"{'generateContent':<17}  model id")
    print("-" * 60)
    for m in models:
        print(f"{'yes' if m['supports_generate_content'] else 'no':<17}  {m['id']}")

    print("\nText models you can use in run_benchmark.py MODELS:")
    for m in usable:
        if not any(k in m["id"] for k in SKIP_KINDS):
            print("  -", m["id"])

    with open("results/available_models.json", "w", encoding="utf-8") as f:
        json.dump({
            "checked_at": datetime.now().isoformat(timespec="seconds"),
            "total_models": len(models),
            "generate_content_models": len(usable),
            "models": models,
        }, f, indent=2)

    print("\nSaved results/available_models.json")


if __name__ == "__main__":
    main()
