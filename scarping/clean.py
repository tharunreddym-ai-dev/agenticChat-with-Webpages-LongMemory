import re
from scarping.get_content import ScrapingError


def clean_text(markdown_text: str) -> str:
    if not markdown_text or not markdown_text.strip():
        raise ScrapingError("No text available to clean.")

    text = markdown_text

    # Remove image syntax but keep the alt text
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)

    # Convert Markdown links to their visible text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Remove email links while keeping the visible text
    text = re.sub(r'\[([^\]]+)\]\(mailto:[^)]+\)', r'\1', text)

    # Remove Markdown heading markers
    text = re.sub(r'^\s{0,3}#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove HTML tags if any remain
    text = re.sub(r'<[^>]+>', ' ', text)

    # Remove obvious webpage UI noise
    noise_patterns = [
        r'\bCLOSE\s*[×x]\b',
        r'\bTap to unmute\b',
        r'\bWatch on\b',
    ]

    for pattern in noise_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Decode common escaped Markdown characters
    text = text.replace(r'\_', '_')
    text = text.replace(r'\*', '*')
    text = text.replace(r'\#', '#')
    text = text.replace(r'\[', '[')
    text = text.replace(r'\]', ']')
    text = text.replace(r'\(', '(')
    text = text.replace(r'\)', ')')

    # Convert repeated backslashes into whitespace
    text = re.sub(r'\\+', '\n', text)

    # Remove leftover Markdown emphasis markers
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
    text = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'\1', text)
    text = re.sub(r'(?<!_)_([^_\n]+)_(?!_)', r'\1', text)

    # Normalize spaces within each line
    text = re.sub(r'[ \t]+', ' ', text)

    # Remove spaces around blank lines
    text = re.sub(r' *\n *', '\n', text)

    # Collapse more than two consecutive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove leading/trailing whitespace
    text = text.strip()

    if not text:
        raise ScrapingError("No readable content remained after cleaning.")

    return text
