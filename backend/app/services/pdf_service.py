from typing import Union
import pymupdf


def extract_text_from_pdf(source: Union[str, bytes]) -> str:
    """Extract full text from a PDF file path or in-memory bytes using PyMuPDF."""
    text_parts = []
    try:
        doc = pymupdf.open(stream=source, filetype="pdf") if isinstance(source, bytes) else pymupdf.open(source)
        with doc:
            for page in doc:
                page_text = page.get_text("text").strip()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")

    if not text_parts:
        raise ValueError(
            "Could not extract any text from the PDF. "
            "The file may be scanned or image-based."
        )

    return "\n\n".join(text_parts)

