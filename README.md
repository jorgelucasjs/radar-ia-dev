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

## Publicar (situação atual)
O site está em **https://jorgelucasjs.github.io/radar-ia-dev/** e é servido a partir do ramo `gh-pages`
(Settings → Pages → "Deploy from a branch" → `gh-pages` / root).
O workflow `radar-semanal` está **desativado** porque o GitHub Actions está bloqueado por um problema de faturação na conta.

Publicar manualmente:
```bash
python3 scripts/build.py
rm -rf /tmp/ghp && git clone -q -b gh-pages https://github.com/jorgelucasjs/radar-ia-dev.git /tmp/ghp
find /tmp/ghp -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} + && cp -r site/. /tmp/ghp/
cd /tmp/ghp && git add -A && git commit -m "Publicar site" && git push
```

Reativar a automação semanal (depois de resolver a faturação):
```bash
gh workflow enable radar-semanal -R jorgelucasjs/radar-ia-dev
gh api -X PUT repos/jorgelucasjs/radar-ia-dev/pages -f build_type=workflow   # Pages passa a usar o workflow
gh workflow run radar-semanal -R jorgelucasjs/radar-ia-dev                    # testar
```

## Newsletter
Formulário inline do Kit "Radar IA Dev" (id 10053474), via POST para `https://app.kit.com/forms/10053474/subscriptions`
(campo `email_address`). Não precisa de chave de API: **nunca** coloque chaves no repositório.
Se o Kit devolver `quarantined`, o visitante é enviado para a verificação anti-spam do Kit.

## Alternativa: Cloudflare Pages
Sem comando de build (ou `python3 scripts/build.py`), pasta de saída `site`.
