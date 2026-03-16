#!/usr/bin/env python3
"""
Debug bulk resume upload issue
Test PDF/DOCX extraction functions to see what's failing
"""

import PyPDF2
import docx
import io
import os

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF - copy of the function from v3_2_compat.py"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        text = text.strip()
        if text:
            print(f"✓ PDF text extracted: {len(text)} characters")
            return text
        else:
            print("✗ PDF text extraction returned empty")
            return "PDF_EMPTY"
    except Exception as e:
        print(f"✗ PDF extraction error: {e}")
        return f"PDF_ERROR: {str(e)}"

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX - copy of the function from v3_2_compat.py"""
    try:
        doc = docx.Document(io.BytesIO(file_content))
        text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        
        text = text.strip()
        if text:
            print(f"✓ DOCX text extracted: {len(text)} characters")
            return text
        else:
            print("✗ DOCX text extraction returned empty")
            return "DOCX_EMPTY"
    except Exception as e:
        print(f"✗ DOCX extraction error: {e}")
        return f"DOCX_ERROR: {str(e)}"

def test_extraction_functions():
    """Test extraction functions on sample files if available"""
    uploads_dir = "uploads"
    
    if not os.path.exists(uploads_dir):
        print(f"❌ Uploads directory doesn't exist: {uploads_dir}")
        return
    
    files = os.listdir(uploads_dir)
    pdf_files = [f for f in files if f.lower().endswith('.pdf')]
    docx_files = [f for f in files if f.lower().endswith(('.docx', '.doc'))]
    
    print(f"Found {len(pdf_files)} PDF files and {len(docx_files)} DOCX files in {uploads_dir}")
    
    # Test PDF files
    for pdf_file in pdf_files[:3]:  # Test max 3 files
        try:
            file_path = os.path.join(uploads_dir, pdf_file)
            print(f"\n🧪 Testing PDF: {pdf_file}")
            
            with open(file_path, 'rb') as f:
                content = f.read()
                result = extract_text_from_pdf(content)
                print(f"Result: {result[:100]}...")
                
        except Exception as e:
            print(f"❌ Error testing {pdf_file}: {e}")
    
    # Test DOCX files
    for docx_file in docx_files[:3]:  # Test max 3 files
        try:
            file_path = os.path.join(uploads_dir, docx_file)
            print(f"\n🧪 Testing DOCX: {docx_file}")
            
            with open(file_path, 'rb') as f:
                content = f.read()
                result = extract_text_from_docx(content)
                print(f"Result: {result[:100]}...")
                
        except Exception as e:
            print(f"❌ Error testing {docx_file}: {e}")

def test_basic_functionality():
    """Test basic PyPDF2 and docx installation"""
    print("🔍 Testing basic library functionality...")
    
    try:
        # Test PyPDF2
        print("✓ PyPDF2 imported successfully")
        print(f"PyPDF2 version: {PyPDF2.__version__ if hasattr(PyPDF2, '__version__') else 'Unknown'}")
        
        # Test python-docx
        print("✓ docx imported successfully")
        print(f"docx module available: {docx}")
        
    except Exception as e:
        print(f"❌ Library test failed: {e}")

if __name__ == "__main__":
    print("🚀 Debugging bulk resume upload issues")
    print("=" * 50)
    
    test_basic_functionality()
    print()
    test_extraction_functions()
    
    print("\n📋 Recommendations:")
    print("1. Check if files in uploads/ are valid PDF/DOCX files")
    print("2. Try uploading a simple text PDF to test")
    print("3. Check console logs when running the actual app")
    print("4. Verify file permissions and file corruption")