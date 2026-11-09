from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/parse-pdf")
async def parse_pdf(file: UploadFile = File(...)):
    # Lemos os bytes do PDF enviado pelo aplicativo
    content = await file.read()
    
    # Abrimos o PDF usando a biblioteca PyMuPDF
    doc = fitz.open(stream=content, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
        
    doc.close()
    
    # ---------------------------------------------------------
    # REGRAS DE EXTRAÇÃO (DETERMINÍSTICO VIA REGEX)
    # Aqui você irá adicionar as regras exatas de como os seus laudos são escritos.
    # Abaixo estão exemplos genéricos para Hemoglobina e Leucócitos.
    # ---------------------------------------------------------
    
    resultados = []
    
    # Exemplo 1: Buscar a palavra Hemoglobina, seguida de números e (opcionalmente) a unidade g/dL
    # Regex explicaçao: (?i) = case insensitive
    match_hemo = re.search(r'(?i)Hemoglobina\s*[:\-]?\s*([\d\,\.]+)\s*(g/dL)?', text)
    if match_hemo:
        valor = match_hemo.group(1).replace(',', '.') # trocando vírgula por ponto para o gráfico
        resultados.append({
            "nome": "Hemoglobina",
            "valor": float(valor) if valor.replace('.','',1).isdigit() else valor,
            "uni": "g/dL",
            "ref": "12 - 17"
        })
        
    # Exemplo 2: Leucócitos
    match_leuco = re.search(r'(?i)Leuc[óo]citos\s*[:\-]?\s*([\d\,\.]+)\s*(/mm3|mm3)?', text)
    if match_leuco:
        valor = match_leuco.group(1).replace(',', '.')
        resultados.append({
            "nome": "Leucócitos",
            "valor": float(valor) if valor.replace('.','',1).isdigit() else valor,
            "uni": "/mm3",
            "ref": "4000 - 10000"
        })

    # Fallback: Se o regex não achar nada, retornamos um aviso em formato de "marcador"
    if not resultados:
        resultados = [
            {"nome": "Falha na Leitura", "valor": 0, "uni": "ERRO", "ref": ""}
        ]

    return {"dadosClinicos": resultados, "raw_text_preview": text[:500]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
