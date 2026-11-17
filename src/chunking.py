import json
import os
from pypdf import PdfReader

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CHUNK_SIZE = 1000   # ek chunk me lagbhag kitne characters
OVERLAP = 200       # do chunks ke beech kitna text common rahe


def split_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    """Lambe text ko chhote, thode-thode overlap wale tukdon me todta hai."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        # shabd ke beech me na kate, isliye pichhle space tak peeche aao
        if end < len(text):
            space = text.rfind(" ", start, end)
            if space > start:
                end = space
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = end - overlap
    return [c for c in chunks if c]


def chunk_pdf(path):
    """Ek PDF ke har page ko padh ke chunks banata hai, page number ke saath."""
    reader = PdfReader(path)
    file_name = os.path.basename(path)
    results = []
    for page_no, page in enumerate(reader.pages, start=1):
        text = " ".join((page.extract_text() or "").split())  # extra space/newline hatao
        for i, chunk in enumerate(split_text(text)):
            # bekar chunks chhod do: bahut chhote (sirf title) ya disclaimer
            if len(chunk) < 100 or "generated using a language model" in chunk:
                continue
            results.append({
                "id": f"{file_name.replace('.', '_')}-p{page_no}-c{i}",
                "source": file_name,
                "page": page_no,
                "content": chunk,
            })
    return results


if __name__ == "__main__":
    all_chunks = []
    for name in sorted(os.listdir(DATA_DIR)):
        if name.lower().endswith(".pdf"):
            chunks = chunk_pdf(os.path.join(DATA_DIR, name))
            print(f"{name}: {len(chunks)} chunks")
            all_chunks.extend(chunks)

    with open(os.path.join(DATA_DIR, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print("Total chunks:", len(all_chunks))
    print("\nExample chunk:\n", json.dumps(all_chunks[0], indent=2)[:600])