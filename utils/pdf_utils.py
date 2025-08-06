from pdfminer.high_level import extract_text

def extract_pdf_text(pdf_file) -> str:
    """
    Extracts text from a PDF file-like object using pdfminer.six.

    Args:
        pdf_file: A file-like object (e.g., Flask uploaded file)

    Returns:
        Extracted text as a string.
    """
    return extract_text(pdf_file)
