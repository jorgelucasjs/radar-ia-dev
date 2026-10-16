#!/usr/bin/env python3
"""
Verificador semanal do Radar IA Dev.

Para cada ferramenta em data/tools.json:
  1. busca de novo a página oficial (source_url + extra_sources);
  2. extrai os valores em dólares que aparecem no texto (ex.: "$20", "$22.80");
  3. compara com os preços guardados em tools.json (preços que sumiram / novos valores);
  4. compara o texto com o snapshot anterior (data/snapshots/<id>.txt) e guarda um diff.
Escreve reports/diff-AAAA-MM-DD.md e .json. NÃO altera tools.json: um humano revê o relatório,
atualiza tools.json e acrescenta uma entrada em data/changes.json.

Opções:
  --update-fx    atualiza o câmbio (open.er-api.com, grátis, sem chave) em tools.json
  --only ID      verifica só uma ferramenta
Código de saída: 0 = sem alterações, 2 = alterações detetadas (útil em CI), 1 = erro.
Só usa a biblioteca padrão do Python.
"""
import json, re, sys, html, hashlib, difflib, datetime, pathlib, argparse, urllib.request
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT/"data/tools.json"; SNAP = ROOT/"data/snapshots"; REP = ROOT/"reports"
UA = "Mozilla/5.0 (compatible; RadarIADev/1.0)"  # alguns sites (ex.: devin.ai) bloqueiam UAs com "Bot"

def fetch(url, tries=3):
    import time
    for i in range(tries):
        try: return _fetch(url)
        except Exception:
            if i == tries - 1: raise
            time.sleep(3 * (i + 1))

def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
        if body[:2] == b"\x1f\x8b":   # alguns servidores enviam gzip mesmo sem Accept-Encoding
            import gzip; body = gzip.decompress(body)
        return r.geturl(), body.decode("utf-8", "ignore")

def to_text(raw):
    raw = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", "\n", raw)
    lines = [re.sub(r"\s+", " ", html.unescape(l)).strip() for l in raw.splitlines()]
    return "\n".join(l for l in lines if l)

PRICE_RE = re.compile(r"(?:US)?\$\s?(\d{1,4}(?:[.,]\d{2})?)(?!\d)")
def prices_in(text):
    out = set()
    for m in PRICE_RE.finditer(text):
        try: out.add(float(m.group(1).replace(",", ".")))
        except ValueError: pass
    return out

def update_fx(data):
    _, raw = fetch("https://open.er-api.com/v6/latest/USD")
    j = json.loads(raw)
    if j.get("result") != "success": raise RuntimeError("FX API falhou")
    old = data["meta"]["fx"]["rates"]
    new = {"USD": 1, **{k: j["rates"][k] for k in ("BRL", "AOA", "EUR")}}
    data["meta"]["fx"].update(rates=new, fetched_at_utc=datetime.datetime.utcfromtimestamp(j["time_last_update_unix"]).strftime("%Y-%m-%dT%H:%M:%SZ"))
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return old, new

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--update-fx", action="store_true"); ap.add_argument("--only")
    a = ap.parse_args()
    data = json.loads(DATA.read_text()); SNAP.mkdir(parents=True, exist_ok=True); REP.mkdir(exist_ok=True)
    today = datetime.date.today().isoformat()
    results, changed_any, md = [], False, [f"# Radar IA Dev — relatório de verificação {today}\n"]
    if a.update_fx:
        try:
            old, new = update_fx(data)
            md.append("## Câmbio\n" + "\n".join(f"- {k}: {old.get(k)} → {new[k]}" for k in ("BRL", "AOA", "EUR")) + "\n")
        except Exception as e:
            md.append(f"## Câmbio\n- ERRO ao atualizar: {e}\n")
    for t in data["tools"]:
        if a.only and t["id"] != a.only: continue
        vplans = [p for p in t["plans"] if p["verified"]]   # planos não verificados não entram no alerta
        stored = {p["price_monthly_usd"] for p in vplans if p["price_monthly_usd"]} | \
                 {p["price_annual_usd_per_month"] for p in vplans if p.get("price_annual_usd_per_month")}
        texts, errors, finals = [], [], []
        for url in [t["source_url"]] + t.get("extra_sources", []):
            try:
                final, raw = fetch(url); finals.append(final); texts.append(f"### {url}\n" + to_text(raw))
            except Exception as e:
                errors.append(f"{url}: {e}")
        r = {"id": t["id"], "name": t["name"], "errors": errors, "final_urls": finals}
        if errors:   # qualquer fonte falhou: não comparar (evita falsos alarmes) e manter o snapshot anterior
            r["status"] = "erro"; results.append(r)
            md.append(f"## ❌ {t['name']}\n- Não foi possível buscar (snapshot anterior mantido): {'; '.join(errors)}\n"); continue
        text = "\n".join(texts); found = prices_in(text)
        js_only = not found   # página sem preços no HTML: provavelmente renderizada por JavaScript
        missing = [] if js_only else sorted(p for p in stored if p not in found)
        new_vals = sorted(p for p in found if p not in stored and p >= 5)
        snapf = SNAP/f"{t['id']}.txt"; prev = snapf.read_text() if snapf.exists() else None
        h_new = hashlib.sha256(text.encode()).hexdigest()
        diff = []
        if prev is not None and hashlib.sha256(prev.encode()).hexdigest() != h_new:
            diff = list(difflib.unified_diff(prev.splitlines(), text.splitlines(), "anterior", "atual", n=1, lineterm=""))
        snapf.write_text(text)
        price_alert = bool(missing)
        r.update(status="alterado" if (price_alert or diff) else ("manual" if js_only else "ok"), js_rendered=js_only, missing_prices=missing, new_dollar_values=new_vals,
                 text_changed=bool(diff), first_snapshot=prev is None, diff_lines=len(diff))
        results.append(r)
        changed_any |= price_alert or bool(diff)
        icon = "🔴" if price_alert else ("🟡" if (diff or js_only) else "🟢")
        md.append(f"## {icon} {t['name']}  ({t['source_url']})")
        if prev is None: md.append("- Primeiro snapshot guardado (sem comparação de texto).")
        if js_only: md.append("- ⚠️ Nenhum preço encontrado no HTML (página renderizada por JavaScript). Verificar manualmente no navegador.")
        if missing: md.append(f"- **Preços guardados que já NÃO aparecem na página:** {', '.join(f'${p:g}' for p in missing)}  → rever planos!")
        if new_vals: md.append(f"- Valores em $ na página que não estão em tools.json (podem ser API, créditos, add-ons): {', '.join(f'${p:g}' for p in new_vals[:20])}")
        if errors: md.append(f"- Fontes com erro: {'; '.join(errors)}")
        if diff:
            md.append(f"- Texto da página mudou ({len(diff)} linhas de diff). Excerto:\n```diff\n" + "\n".join(diff[:80]) + "\n```")
        if not (prev is None or missing or diff or js_only): md.append("- Sem alterações.")
        md.append("")
    md.append("---\nPróximo passo: rever os itens 🔴/🟡, atualizar data/tools.json (campo `checked`) e acrescentar uma entrada em data/changes.json. Depois: `python3 scripts/build.py`.")
    (REP/f"diff-{today}.md").write_text("\n".join(md))
    (REP/f"diff-{today}.json").write_text(json.dumps({"date": today, "results": results}, ensure_ascii=False, indent=2))
    print("\n".join(md[:1]) + f"\nRelatório: reports/diff-{today}.md  ({sum(r['status']=='alterado' for r in results)} alterados, {sum(r['status']=='erro' for r in results)} erros)")
    sys.exit(2 if changed_any else 0)

if __name__ == "__main__":
    try: main()
    except SystemExit: raise
    except Exception as e: print("ERRO:", e); sys.exit(1)
