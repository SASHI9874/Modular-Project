import io
from pypdf import PdfReader

def extract_text_from_bytes(file_content: bytes, filename: str) -> dict:
    """
    Core logic: Reads bytes, parses PDF, returns text.
    Returns a dictionary matching the 'outputs' spec in feature.spec.json.
    """
    try:
        # Create a file-like object from bytes
        pdf_file = io.BytesIO(file_content)
        reader = PdfReader(pdf_file)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        return {
            "file_text": text.strip(),
            "filename": filename
        }
    except Exception as e:
        return {
            "file_text": f"Error reading PDF: {str(e)}",
            "filename": filename
        }