import pymupdf


def extract_text_from_pdf(file_path: str) -> str:
    """Extract full text from a PDF file using PyMuPDF."""
    text_parts = []
    try:
        with pymupdf.open(file_path) as doc:
            for page_num, page in enumerate(doc):
                page_text = page.get_text("text")
                if page_text.strip():
                    text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")

    if not text_parts:
        raise ValueError(
            "Could not extract any text from the PDF. "
            "The file may be scanned or image-based."
        )

    return "\n\n".join(text_parts)

