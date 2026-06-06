import fitz # PyMuPDF
import base64

def extract_text_and_images(pdf_path: str):
    text_content = ""
    first_image_b64 = None
    
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_content += page.get_text()
            
            # Extract first image found in PDF to send to multimodal LLM
            if not first_image_b64:
                image_list = page.get_images(full=True)
                if image_list:
                    xref = image_list[0][0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    first_image_b64 = base64.b64encode(image_bytes).decode("utf-8")
                    
        return text_content, first_image_b64
    except Exception as e:
        print(f"PDF Extraction error: {e}")
        return "", None
