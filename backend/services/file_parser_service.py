import base64
from io import BytesIO
from pypdf import PdfReader
from docx import Document
from core.config import settings
from groq import Groq

class FileParserService:
    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)

    def parse_text(self, file_bytes: bytes) -> str:
        return file_bytes.decode('utf-8', errors='ignore')

    def parse_pdf(self, file_bytes: bytes) -> str:
        reader = PdfReader(BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text

    def parse_docx(self, file_bytes: bytes) -> str:
        doc = Document(BytesIO(file_bytes))
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text

    def parse_image(self, file_bytes: bytes, filename: str) -> str:
        base64_image = base64.b64encode(file_bytes).decode('utf-8')
        
        mime_type = "image/jpeg"
        if filename.lower().endswith('.png'):
            mime_type = "image/png"

        response = self.groq_client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all text from this image and describe any charts, diagrams, or important visual information in detail so it can be indexed for search."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=1024,
        )
        return response.choices[0].message.content

    def parse_file(self, file_bytes: bytes, filename: str) -> str:
        ext = filename.lower().split('.')[-1]
        
        if ext in ['txt', 'md', 'csv']:
            return self.parse_text(file_bytes)
        elif ext == 'pdf':
            return self.parse_pdf(file_bytes)
        elif ext == 'docx':
            return self.parse_docx(file_bytes)
        elif ext in ['png', 'jpg', 'jpeg']:
            return self.parse_image(file_bytes, filename)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
