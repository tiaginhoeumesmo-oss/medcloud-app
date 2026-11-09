# MedCloud

Portal para laboratórios enviarem laudos de exames em PDF. A API lê o PDF, pega os valores dos exames e salva no Supabase pro paciente ver no app.

## Pastas

- `portal-laboratorio/` - projeto principal (site + API em `api/index.py`)
- `medcloud-python-backend/` - versão antiga da API, o `api/index.py` é igual ao do portal

## Rodando local

API:

```
cd portal-laboratorio
pip install -r requirements.txt uvicorn
uvicorn api.index:app --port 8000
```

Site: abrir o `portal-laboratorio/index.html` no navegador. Login de teste `admin` / `1234`.

A leitura automática do PDF só funciona no deploy da Vercel, local tem que preencher os valores na mão.

## Testes

Os bugs que encontrei testando estão em [BUGS.md](BUGS.md).
