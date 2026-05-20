# app/utils/arxiv.py
import re


def extract_arxiv_id(url: str) -> str | None:
    """
    Extracts arxiv ID from various URL formats:
    https://arxiv.org/abs/2301.00001
    https://arxiv.org/pdf/2301.00001
    2301.00001 (raw ID)
    """
    patterns = [r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", r"^(\d{4}\.\d{4,5})$"]
    for pattern in patterns:
        match = re.search(pattern, url.strip())
        if match:
            return match.group(1)
    return None
