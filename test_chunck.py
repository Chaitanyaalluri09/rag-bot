from app.pdf_reader import read_pdf
from app.chunker import chunk_pages

pages = read_pdf("data/mydoc.pdf")
chunks = chunk_pages(pages)

print("Pages with text:", len(pages))
print("Total chunks:", len(chunks))

lengths = [len(c["content"]) for c in chunks]
print("Shortest chunk:", min(lengths), "characters")
print("Longest chunk:", max(lengths), "characters")

print("\n--- First chunk ---")
print(chunks[0])
print("\n--- A chunk from the middle ---")
print(chunks[len(chunks) // 2])