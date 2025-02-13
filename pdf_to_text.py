import os
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import logging

class PDFToTextConverter:
    def __init__(self, tesseract_path: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        if tesseract_path:
            if not os.path.exists(tesseract_path):
                raise FileNotFoundError(f"Tesseract executable not found at: {tesseract_path}")
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        self.custom_config = '--oem 3 --psm 6 -c preserve_interword_spaces=1'
    
    def convert_pdf_to_text(self, pdf_path: str, output_path: str = None) -> str:
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            self.logger.info(f"Converting PDF: {pdf_path}")
            
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            try:
                images = convert_from_path(
                    pdf_path,
                    poppler_path=r"C:\Program Files\poppler-23.11.0\Library\bin",
                    dpi=300
                )
            except Exception as e:
                self.logger.error(f"Error converting PDF to images: {str(e)}")
                raise
            
            full_text = []
            for i, image in enumerate(images):
                self.logger.info(f"Processing page {i+1}/{len(images)}")
                
                try:
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    text = pytesseract.image_to_string(
                        image,
                        config=self.custom_config,
                        lang='eng'
                    )
                    
                    # Encode and decode to handle special characters
                    text = text.encode('utf-8', errors='ignore').decode('utf-8')
                    
                    if text.strip():
                        full_text.append(text.strip())
                except Exception as e:
                    self.logger.error(f"Error processing page {i+1}: {str(e)}")
                    continue
            
            if not full_text:
                self.logger.warning("No text was extracted from the PDF")
                return ""
            
            combined_text = '\n\n'.join(full_text)
            
            if output_path:
                self.save_text_to_file(combined_text, output_path)
            
            return combined_text
            
        except Exception as e:
            self.logger.error(f"Error converting PDF: {str(e)}")
            raise
    
    def save_text_to_file(self, text: str, output_path: str):
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write with utf-8 encoding and error handling
            with open(output_path, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(text)
            self.logger.info(f"Text saved to: {output_path}")
        except Exception as e:
            self.logger.error(f"Error saving text: {str(e)}")
            raise

def main(filename):
    try:
        converter = PDFToTextConverter()
        
        pdf_path = os.path.join(r"D:\MAI\THWS\Hiwi\data\inputs", f"{filename}")
        output_path = os.path.join(r"D:\MAI\THWS\Hiwi\data\outputs", f"{filename}.txt")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Input PDF not found: {pdf_path}")
        
        text = converter.convert_pdf_to_text(pdf_path, output_path)
        
        if text:
            print("\nExtracted text preview:")
            print("-" * 50)
            # Encode and decode the preview text as well
            preview_text = text[:500].encode('utf-8', errors='ignore').decode('utf-8')
            print(preview_text + "..." if len(text) > 500 else preview_text)
            print("-" * 50)
        else:
            print("No text was extracted from the PDF")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":

    WD = os.getcwd()



    for filename in os.listdir(r"D:\MAI\THWS\Hiwi\data\inputs"):
        if filename.endswith(".pdf"):
            main(filename)
            

