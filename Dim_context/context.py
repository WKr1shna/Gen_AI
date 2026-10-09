import os
from typing import List
from dotenv import load_dotenv
from PIL import Image
import pytesseract
import fitz

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# 1. Load environment variables (GOOGLE_API_KEY from .env)
load_dotenv()

# Configure Tesseract binary path
for p in ["/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract", "/usr/bin/tesseract"]:
    if os.path.exists(p):
        pytesseract.pytesseract.tesseract_cmd = p
        break

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}

def extract_text_from_image(image_path: str) -> str:
    """Extracts text from an image file using OCR."""
    try:
        # Try pytesseract first
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        if text.strip():
            return text
    except Exception:
        pass

    # Fallback to PyMuPDF image OCR
    try:
        doc = fitz.open(image_path)
        pdf_bytes = doc.convert_to_pdf()
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        ocr_tp = pdf_doc[0].get_textpage_ocr(language="eng", dpi=150, full=True)
        text = ocr_tp.extractTEXT()
        return text
    except Exception:
        return ""

def load_documents(file_path: str) -> List[Document]:
    """Loads text documents from either a PDF file or an Image file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    # Case 1: PDF Document
    if ext == ".pdf":
        print(f"Loading PDF from: {file_path}...")
        loader = PyPDFLoader(file_path=file_path)
        docs = loader.load()

        # If PDF has minimal/empty selectable text (scanned PDF), apply OCR fallback
        total_text = "".join(d.page_content for d in docs).strip()
        if len(total_text) < 15:
            print("PDF appears scanned. Running OCR on pages...")
            doc = fitz.open(file_path)
            docs = []
            for idx, page in enumerate(doc):
                ocr_tp = page.get_textpage_ocr(language="eng", dpi=150, full=True)
                page_text = ocr_tp.extractTEXT()
                docs.append(Document(
                    page_content=page_text,
                    metadata={"source": file_path, "page": idx + 1, "type": "scanned_pdf"}
                ))
        return docs

    # Case 2: Image File (PNG, JPG, JPEG, WEBP, etc.)
    elif ext in IMAGE_EXTENSIONS:
        print(f"Loading Image and running OCR on: {file_path}...")
        extracted_text = extract_text_from_image(file_path)
        if not extracted_text.strip():
            extracted_text = "[No text detected in image]"
            print("Warning: OCR did not detect readable text in image.")
        else:
            print(f"Successfully extracted {len(extracted_text)} characters from image via OCR.")

        return [Document(
            page_content=extracted_text,
            metadata={"source": file_path, "type": "image"}
        )]
    else:
        raise ValueError(f"Unsupported file format: {ext}. Supported formats: PDF, PNG, JPG, JPEG, WEBP, TIFF, BMP")

def process_and_store_document(file_path: str, persist_directory: str = "./chroma_db"):
    """
    Loads a PDF or Image, chunks the text, embeds using models/text-embedding-004,
    and stores vectors in a Chroma vector store.
    """
    # 2. Load documents (PDF or Image)
    docs = load_documents(file_path)

    # 3. Split document into chunks
    print("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Generated {len(chunks)} text chunks.")

    # 4. Initialize embedding model
    print("Initializing Google Generative AI Embeddings (models/text-embedding-004)...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

    # 5. Create Chroma vector store and insert chunks
    print("Generating embeddings and storing in Chroma vector store...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )

    # 6. Confirm success with vector count and directory path
    abs_persist_path = os.path.abspath(persist_directory)
    print(f"\n[SUCCESS] Successfully inserted {len(chunks)} vectors into Chroma vector store.")
    print(f"[STORE LOCATION] {abs_persist_path}")

    return vector_store

if __name__ == "__main__":
    # Example usage: pass a PDF or an Image file path
    sample_path = "sample.pdf"  # or e.g., "document.png", "receipt.jpg"
    
    if os.path.exists(sample_path):
        process_and_store_document(sample_path)
    else:
        print(f"Please provide a valid PDF or Image file path (e.g., '{sample_path}').")