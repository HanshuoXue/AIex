import os
import PyPDF2
import docx
from typing import Dict, Any
from promptflow import tool


@tool
def cv_extractor(file_path: str) -> str:
    """
    Extract text from CV file (PDF or Word)
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"

        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.pdf':
            return extract_from_pdf(file_path)
        elif file_extension in ['.doc', '.docx']:
            return extract_from_word(file_path)
        else:
            return f"Error: Unsupported file type {file_extension}"

    except Exception as e:
        return f"Error extracting text: {str(e)}"


def extract_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"

            return clean_text(text)
    except Exception as e:
        return f"Error reading PDF: {str(e)}"


def extract_from_word(file_path: str) -> str:
    """Extract text from Word file"""
    try:
        doc = docx.Document(file_path)
        text = ""

        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"

        return clean_text(text)
    except Exception as e:
        return f"Error reading Word document: {str(e)}"


def clean_text(text: str) -> str:
    """Clean and normalize extracted text"""
    # Remove extra whitespace
    text = ' '.join(text.split())

    # Remove common PDF artifacts
    text = text.replace('\x00', '')  # Remove null characters
    text = text.replace('\ufeff', '')  # Remove BOM

    # Normalize line breaks
    text = text.replace('\n', ' ').replace('\r', ' ')

    # Remove multiple spaces
    while '  ' in text:
        text = text.replace('  ', ' ')

    return text.strip()
