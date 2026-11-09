import fitz
import re
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/parse-pdf")
@app.post("/api/process-pdf")
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
    
    # Função auxiliar para encontrar padrões de chaves
    def extract_value(pattern, text):
        match = re.search(r"(?:" + pattern + r")\s*[:\-]?\s*([\d,\.]+)", text, re.IGNORECASE)
        if match and match.group(1):
            return match.group(1).replace(',', '.')
        return None

    # Função auxiliar para Linfócitos etc (ignorar % e pegar o absoluto maior)
    def extract_absolute(pattern, text):
        line_match = re.search(r"(?:" + pattern + r").*", text, re.IGNORECASE)
        if line_match:
            line = line_match.group(0)
            nums = re.findall(r"\d+(?:[,\.]\d+)?", line)
            if nums:
                floats = [float(n.replace(',', '.')) for n in nums]
                if floats:
                    return str(max(floats))
        return None

    # Encontrar Usuário e Senha de Imagem (PACS)
    user_match = re.search(r"(?:Usu[aá]rio|Login|Accession(?: Number)?|Protocolo)\s*[:\-]?\s*([\w\d]+)", text, re.IGNORECASE)
    pass_match = re.search(r"(?:Senha|Password|Pin)\s*[:\-]?\s*([\w\d@#$%&*!]+)", text, re.IGNORECASE)

    # 6 Categorias Mapeadas
    patterns = {
        # 1. Rotina Básica
        "Hemoglobina": (r"Hemoglobina", "g/dL", False),
        "Hematócrito": (r"Hemat[oó]crito", "%", False),
        "Leucócitos": (r"Leuc[oó]citos", "/mm³", False),
        "Plaquetas": (r"Plaquetas", "/mm³", False),
        "Glicose": (r"Glic(?:emia|ose)(?:\s*em\s*jejum)?", "mg/dL", False),
        "Colesterol Total": (r"Colesterol\s*Total", "mg/dL", False),
        "Colesterol HDL": (r"Colesterol\s*HDL|HDL\s*-?\s*Colesterol", "mg/dL", False),
        "Colesterol LDL": (r"Colesterol\s*LDL|LDL\s*-?\s*Colesterol", "mg/dL", False),
        "Colesterol VLDL": (r"Colesterol\s*VLDL|VLDL\s*-?\s*Colesterol", "mg/dL", False),
        "Triglicerídeos": (r"Triglicer[ií]deos?", "mg/dL", False),
        "Ureia": (r"Ureia", "mg/dL", False),
        "Creatinina": (r"Creatinina", "mg/dL", False),
        "eTFG": (r"(?:eTFG|Taxa de Filtra..o)", "mL/min", False),
        "Sódio": (r"S[oó]dio", "mEq/L", False),
        "Potássio": (r"Pot[aá]ssio", "mEq/L", False),
        "Cálcio Total": (r"C[aá]lcio\s*(?:Total)?", "mg/dL", False),
        "Magnésio": (r"Magn[eé]sio", "mg/dL", False),
        "Cloreto": (r"Cloreto|Cloro", "mEq/L", False),

        # 2. Avaliação Sistêmica e Metabólica
        "TGO / AST": (r"TGO|AST|Aspartato", "U/L", False),
        "TGP / ALT": (r"TGP|ALT|Alanina", "U/L", False),
        "Gama-GT": (r"Gama[- ]?GT|GGT", "U/L", False),
        "Fosfatase Alcalina": (r"Fosfatase\s*Alcalina|FA", "U/L", False),
        "Bilirrubina Total": (r"Bilirrubina\s*Total", "mg/dL", False),
        "Bilirrubina Direta": (r"Bilirrubina\s*Direta", "mg/dL", False),
        "Bilirrubina Indireta": (r"Bilirrubina\s*Indireta", "mg/dL", False),
        "Hemoglobina Glicada": (r"Hemoglobina\s*Glicada|HbA1c", "%", False),
        "Ácido Úrico": (r"[AÁ]cido\s*[UÚ]rico", "mg/dL", False),
        "Tempo de Protrombina": (r"Tempo\s*de\s*Protrombina|TAP", "seg", False),
        "INR": (r"INR", "", False),
        "TTPA": (r"TTPA|Tempo de Tromboplastina", "seg", False),
        "Proteína C Reativa": (r"Prote[ií]na\s*C\s*Reativa|PCR", "mg/L", False),
        "Velocidade de Hemossedimentação": (r"Velocidade\s*de\s*Hemossedimenta..o|VHS", "mm/h", False),
        "TSH": (r"TSH|Horm.nio\s*Tireoestimulante", "µUI/mL", False),
        "T4 Livre": (r"T4\s*Livre|Tiroxina\s*Livre", "ng/dL", False),
        "Proteínas Totais": (r"Prote[ií]nas\s*Totais", "g/dL", False),
        "Albumina": (r"Albumina", "g/dL", False),
        "Globulinas": (r"Globulinas", "g/dL", False),

        # 3. Nutricional e Hormonal
        "Ferro Sérico": (r"Ferro(?:S[eé]rico)?", "µg/dL", False),
        "Ferritina": (r"Ferritina", "ng/mL", False),
        "TIBC": (r"TIBC|Capacidade\s*Total", "µg/dL", False),
        "Vitamina D": (r"Vitamina\s*D(?:(?:25|3|\-OH)+)?", "ng/mL", False),
        "Vitamina B12": (r"Vitamina\s*B12", "pg/mL", False),
        "FSH": (r"FSH|Horm.nio\s*Fol.culo", "mUI/mL", False),
        "LH": (r"LH|Horm.nio\s*Luteinizante", "mUI/mL", False),
        "Prolactina": (r"Prolactina", "ng/mL", False),
        "Estradiol": (r"Estradiol", "pg/mL", False),
        "Testosterona Total": (r"Testosterona(?:\s*Total)?", "ng/dL", False),
        "Testosterona Livre": (r"Testosterona\s*Livre", "ng/dL", False),
        "Progesterona": (r"Progesterona", "ng/mL", False),
        "Cortisol Basal": (r"Cortisol(?:\s*Basal|\s*S[eé]rico)?", "µg/dL", False),

        # 5. Biomarcadores Específicos e Autoimunes
        "Troponina I ou T": (r"Troponina\s*(?:I|T)", "ng/mL", False),
        "CK-MB": (r"CK[- ]?MB", "U/L", False),
        "BNP": (r"BNP|NT-proBNP", "pg/mL", False),
        "D-Dímero": (r"D[- ]?D[ií]mero", "ng/mL", False),
        "PSA Livre": (r"PSA\s*Livre", "ng/mL", False),
        "PSA Total": (r"PSA(?:\s*Total)?", "ng/mL", False),
        "CEA": (r"CEA|Ant[ií]geno\s*Carcinoembrion[aá]rio", "ng/mL", False),
        "CA 125": (r"CA\s*125", "U/mL", False),
        "CA 19-9": (r"CA\s*19[- ]?9", "U/mL", False),
        "Alfa-fetoproteína": (r"Alfa[- ]?fetoprote[ií]na|AFP", "ng/mL", False),

        # Exceções Absolutas
        "Linfócitos Absolutos": (r"Linf[oó]citos", "/mm³", True),
        "Monócitos Absolutos": (r"Mon[oó]citos", "/mm³", True),
        "Eosinófilos Absolutos": (r"Eosin[oó]filos", "/mm³", True),
        "Basófilos Absolutos": (r"Bas[oó]filos", "/mm³", True),
    }
    
    dadosClinicos = []
    
    for nome, (pattern, uni, use_absolute) in patterns.items():
        if use_absolute:
            val = extract_absolute(pattern, text)
        else:
            val = extract_value(pattern, text)
            
        if val is not None:
            dadosClinicos.append({
                "nome": nome,
                "valor": val,
                "uni": uni,
                "tipo": "lab"
            })
    
    # Se houver usuário e senha, consideramos "pacs" (Imagem)
    if user_match and pass_match:
        usr = user_match.group(1)
        pwd = pass_match.group(1)
        # Tentar adivinhar a URL do PACS (se estiver no texto)
        url_match = re.search(r"https?://[\w\-\.]+(?:/[\w\-\./?%&=]*)?", text)
        pacs_url = url_match.group(0) if url_match else ""
        
        dadosClinicos.append({
            "nome": "Acesso PACS",
            "valor": "Credenciais encontradas",
            "uni": "",
            "tipo": "pacs",
            "usuario": usr,
            "senha": pwd,
            "url": pacs_url
        })
            
    # Encontrar ID do Paciente (geralmente de 5 a 8 dígitos)
    patient_match = re.search(r"(?:ID(?: do)? Paciente|C[oó]digo(?: do)? Paciente|Registro|Paciente)\s*[:\-]?\s*(\d{5,8})", text, re.IGNORECASE)
    patient_id = patient_match.group(1) if patient_match else None

    return {"dadosClinicos": dadosClinicos, "patientId": patient_id}
