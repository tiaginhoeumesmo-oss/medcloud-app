# Bugs encontrados

## Graves

**Leucócitos e plaquetas saem 1000x menores**
Laudo escreve `4.500` e o sistema salva `4.5`. Plaquetas `250.000` vira `250`. O ponto de milhar está sendo lido como decimal.

**Linfócitos, monócitos, eosinófilos e basófilos pegam o número errado**
O código pega o maior número da linha, que geralmente é o valor de referência.
Ex: `Linfócitos 30 % 1350 /mm³ 900 a 2900` salva 2900.

**Login não protege nada**
Usuário e senha ficam no `app.js` (só em base64), qualquer um descobre olhando o código. E o upload pro Supabase funciona mesmo sem logar.

**Laudos ficam com link público**
O PDF vai pro bucket `laudos` com `getPublicUrl`, então quem tiver o link abre o exame.

**Senha do PACS salva no banco**
Se o PDF tiver usuário e senha do PACS, vai pro banco em texto puro.

## Menores

- `Ferro Sérico` nunca é lido, falta `\s*` no regex: `Ferro(?:S[eé]rico)?`
- O ID do paciente pode pegar outro número (qualquer `Registro` ou `Paciente` seguido de 5 a 8 dígitos)
- CORS liberado pra qualquer origem e sem limite de tamanho do PDF
- `api/index.py` repetido nas duas pastas
