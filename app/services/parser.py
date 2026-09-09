import pymupdf
from pathlib import Path


def extract_pdf_text(file_path: str | Path) -> list[dict]:
    """
    Extract text from a PDF page by page.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    pages = []

    with pymupdf.open(file_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()

            pages.append(
                {
                    "page_number": page_number,
                    "text": text,
                }
            )

    return pages