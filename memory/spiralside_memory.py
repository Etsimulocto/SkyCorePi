# =============================================================================
# SKYCORE PI
# FILE: memory/spiralside_memory.py
# PURPOSE: Local Spiralside archive search/context loader
# FORMAT: bloomcore/v1.0
# CREW: Sky (local), Architect (root)
# =============================================================================

import os
import re

SPIRALSIDE_PATH = "/home/quarterbitgames/Bloomcore/GitHub/spiralside"

TEXT_EXTENSIONS = {
    ".txt", ".md", ".json", ".html", ".css", ".js", ".py", ".lua"
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".next", "dist", "build"
}


def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_spiralside_context(query, max_chars=5000, max_files=6):
    query_words = [w.lower() for w in query.split() if len(w) > 2]
    matches = []

    if not os.path.exists(SPIRALSIDE_PATH):
        return "", ["Spiralside archive not found."]

    for root, dirs, files in os.walk(SPIRALSIDE_PATH):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for file in files:
            ext = os.path.splitext(file)[1].lower()

            if ext not in TEXT_EXTENSIONS:
                continue

            path = os.path.join(root, file)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except Exception:
                continue

            lowered = text.lower()
            score = sum(lowered.count(word) for word in query_words)

            if score > 0:
                snippet = clean_text(text[:2500])
                matches.append((score, path, snippet))

    matches.sort(reverse=True, key=lambda x: x[0])

    context = ""
    sources = []

    for score, path, snippet in matches[:max_files]:
        rel = path.replace(SPIRALSIDE_PATH + "/", "")
        sources.append(rel)
        context += f"\n\n--- SOURCE: {rel} ---\n{snippet}"

    return context[:max_chars], sources
