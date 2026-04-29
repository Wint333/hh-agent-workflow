import re
from typing import Iterable, List


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def contains_any(text: str, words: Iterable[str]) -> bool:
    return any(word in text for word in words)


def unique_merge(old: List[str], new: List[str]) -> List[str]:
    result = list(old)
    for item in new:
        clean = item.strip()
        if clean and clean not in result:
            result.append(clean)
    return result[:8]
