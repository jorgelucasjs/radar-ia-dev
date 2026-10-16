# Radar IA Dev — v1

Comparador em português de preços e limites de ferramentas de IA para programar
(Cursor, Claude Code, Codex, Copilot, Gemini/Antigravity, Windsurf, TRAE, Kiro, Amazon Q, OpenCode Go, Zed).
O site é 100% estático e não precisa de servidor. Só usa Python (biblioteca padrão).

## Estrutura
- `data/tools.json`: ferramentas, planos, limites, fonte, data de verificação, câmbio (BRL/AOA/EUR)
- `data/changes.json`: registo de mudanças (página "Mudanças")
- `scripts/build.py`: gera `site/`. **Editar o bloco CONFIG** (domínio, endpoint da newsletter, e-mails)
- `scripts/check_prices.py`: volta a buscar as fontes oficiais e escreve `reports/diff-AAAA-MM-DD.md/.json`
- `scripts/seed_data.py`: dados iniciais (uma única vez)
- `src/`: CSS e JS (câmbio, filtros, ordenação)
- `newsletter/issue-001.md`: rascunho da 1.ª edição
- `.github/workflows/weekly.yml`: verificação semanal + deploy no GitHub Pages

## Uso
```bash
python3 scripts/build.py                     # gera site/
cd site && python3 -m http.server 8000       # pré-visualizar em http://localhost:8000
python3 scripts/check_prices.py              # 0 = sem mudanças, 2 = mudanças, 1 = erro
python3 scripts/check_prices.py --update-fx  # também atualiza o câmbio
python3 scripts/check_prices.py --only kiro
```
Rotina semanal: correr o check → ler o relatório (🔴 = preço guardado já não aparece, 🟡 = rever manualmente)
→ editar `tools.json` (+ `checked`) e `changes.json` → `build.py` → publicar.
O checker **nunca** edita os preços sozinho.

## Publicar
- **GitHub Pages:** criar o repositório, fazer push e escolher Settings → Pages → "GitHub Actions".
- **Cloudflare Pages:** sem comando de build (ou `python3 scripts/build.py`), pasta de saída `site`.

Os links são relativos, por isso o site também funciona num subcaminho (`usuario.github.io/radar-ia-dev/`).
