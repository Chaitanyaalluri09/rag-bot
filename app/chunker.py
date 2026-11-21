def split_text(text, chunk_size=1000, overlap=150):
    """Cut one long text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size

        # If we're not at the end, try to finish at a sentence boundary
        if end < len(text):
            boundary = text.rfind(". ", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break
        start = end - overlap  # step back to create the overlap
    return chunks


def chunk_pages(pages, chunk_size=1000, overlap=150):
    """Chunk every page and remember which page each chunk came from."""
    all_chunks = []
    for page_number, text in pages:
        for index, piece in enumerate(split_text(text, chunk_size, overlap)):
            all_chunks.append(
                {"page": page_number, "chunk_index": index, "content": piece}
            )
    return all_chunks