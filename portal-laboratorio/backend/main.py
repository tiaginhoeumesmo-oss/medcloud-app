import fitz
import re
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process-pdf")
async def process_pdf(file: UploadFile = File(...)):
    contents = await file.read()
    
    # Abrir o PDF com PyMuPDF
    try:
        doc = fitz.open(stream=contents, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
            
        doc.close()
    except Exception as e:
        return {"error": str(e)}
    
    # Extrair os dados com Regex
    def extract_value(pattern, text):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).replace(',', '.')
        return ""

    hemo = extract_value(r"Hemoglobina\s*[:\-]?\s*([\d,\.]+)", text)
    leuco = extract_value(r"Leuc[oó]citos\s*[:\-]?\s*([\d,\.]+)", text)
    glicose = extract_value(r"Glicose\s*[:\-]?\s*([\d,\.]+)", text)
    potassio = extract_value(r"Pot[aá]ssio\s*[:\-]?\s*([\d,\.]+)", text)
    
    return {
        "hemoglobina": hemo,
        "leucocitos": leuco,
        "glicose": glicose,
        "potassio": potassio,
        "text_preview": text[:200] # Para debug
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
