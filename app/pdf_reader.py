from pypdf import PdfReader


def read_pdf(path):
    """Return a list of (page_number, text) for every page that has text."""
    reader = PdfReader(path)
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = " ".join(text.split())  # collapse extra spaces and newlines
        if text:
            pages.append((page_number, text))
    return pages