#!/usr/bin/env python3
"""Gera o site estático em ./site a partir de data/*.json. Sem dependências externas."""
import json, html, shutil, pathlib, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "site"
# ---- CONFIG (alterar antes de publicar) ----
SITE_URL = "https://jorgelucasjs.github.io/radar-ia-dev"   # GitHub Pages (sub-caminho); trocar se houver domínio próprio
NEWSLETTER_ACTION = "https://example.com/PLACEHOLDER-newsletter-endpoint"  # PLACEHOLDER: trocar pelo endpoint do Buttondown/Beehiiv/Kit
CORRECTION_EMAIL = "correcoes@PLACEHOLDER.radariadev.com"                 # PLACEHOLDER
SPONSOR_EMAIL = "anuncie@PLACEHOLDER.radariadev.com"                      # PLACEHOLDER
# --------------------------------------------
data = json.loads((ROOT/"data/tools.json").read_text())
changes = json.loads((ROOT/"data/changes.json").read_text())["entries"]
meta, tools = data["meta"], data["tools"]
E = lambda s: html.escape("" if s is None else str(s))
def d_pt(iso): y,m,d = iso.split("-"); return f"{d}/{m}/{y}"
def rel(depth): return "../"*depth
def cur_switch(): return '<div class="cur" role="group" aria-label="Moeda">' + "".join(
    f'<button type="button" data-c="{c}">{l}</button>' for c,l in [("USD","US$"),("BRL","R$"),("AOA","Kz"),("EUR","€")]) + "</div>"
def price_span(usd):
    v = "" if usd is None else usd
    return f'<span data-usd="{v}">{"—" if usd is None else ("Grátis" if usd==0 else f"US$ {usd}")}</span>'
def layout(title, desc, path, body, depth, on=""):
    url = SITE_URL.rstrip("/") + "/" + path
    nav = [("", "Comparar"), ("mudancas/", "Mudanças"), ("anuncie/", "Anuncie aqui")]
    navh = "".join(f'<a href="{rel(depth)}{p}"{" class=on" if on==p else ""}>{l}</a>' for p,l in nav)
    fx = json.dumps({"rates": meta["fx"]["rates"]})
    return f"""<!doctype html><html lang="pt"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}"><meta name="robots" content="index,follow">
<meta property="og:type" content="website"><meta property="og:site_name" content="Radar IA Dev">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{url}">
<meta property="og:locale" content="pt_BR"><meta property="og:locale:alternate" content="pt_PT">
<meta name="twitter:card" content="summary"><meta name="theme-color" content="#0b1020">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📡</text></svg>">
<link rel="stylesheet" href="{rel(depth)}assets/style.css"></head><body>
<header class="top"><div class="wrap"><a class="logo" href="{rel(depth)}">📡 Radar <span>IA</span> Dev</a><nav class="main">{navh}</nav></div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap"><div>© {datetime.date.today().year} Radar IA Dev · Preços de ferramentas de IA para programar, em português.</div>
<div><a href="mailto:{CORRECTION_EMAIL}?subject=Corre%C3%A7%C3%A3o%20Radar%20IA%20Dev">Envie uma correção</a> · <a href="{rel(depth)}data/tools.json">Dados (JSON)</a> · <a href="{rel(depth)}anuncie/">Anuncie</a></div></div></footer>
<script>window.RADAR_FX={fx};</script><script src="{rel(depth)}assets/app.js" defer></script></body></html>"""
def newsletter_block():
    return f"""<section class="news" id="newsletter"><h2>📬 Radar de segunda-feira</h2>
<p>Toda segunda: o que mudou nos preços e limites do Cursor, Claude Code, Codex, Copilot e companhia, em 3 minutos de leitura. Grátis.</p>
<form action="{NEWSLETTER_ACTION}" method="post" target="_blank"><input type="email" name="email" placeholder="o.seu@email.com" required aria-label="Email">
<button class="btn" type="submit">Quero receber</button></form>
<div class="placeholder">⚠️ PLACEHOLDER: formulário ainda não ligado a um serviço de newsletter.</div></section>"""
fx = meta["fx"]
_pt = lambda v, d: f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
fxline = f'Câmbio: 1 US$ = R$ {_pt(fx["rates"]["BRL"],2)} · Kz {_pt(fx["rates"]["AOA"],0)} · € {_pt(fx["rates"]["EUR"],3)} (fonte: <a href="{fx["source"]}">open.er-api.com</a>, {fx["fetched_at_utc"][:10]})'
if OUT.exists(): shutil.rmtree(OUT)
(OUT/"assets").mkdir(parents=True); (OUT/"data").mkdir()
shutil.copy(ROOT/"src/style.css", OUT/"assets/style.css"); shutil.copy(ROOT/"src/app.js", OUT/"assets/app.js")
shutil.copy(ROOT/"data/tools.json", OUT/"data/tools.json"); shutil.copy(ROOT/"data/changes.json", OUT/"data/changes.json")
pages = []
# ---- Home
rows = []
for t in tools:
    for p in t["plans"]:
        badges = ('<span class="badge free">grátis</span> ' if p["price_monthly_usd"]==0 else "") + \
                 ('<span class="badge ok">verificado</span>' if p["verified"] else f'<span class="badge no" title="{E(p.get("verification_note"))}">não verificado</span>')
        ann = f'<small>anual: <span data-usd="{p["price_annual_usd_per_month"]}">US$ {p["price_annual_usd_per_month"]}</span>/mês</small>' if p.get("price_annual_usd_per_month") else ""
        pu = "<small>por utilizador</small>" if p.get("per_user") else ""
        pr = "" if p["price_monthly_usd"] is None else p["price_monthly_usd"]
        rows.append(f'<tr data-price="{pr}" data-tool="{E(t["name"])}" data-plan="{E(p["name"])}" data-ver="{1 if p["verified"] else 0}">'
            f'<td class="tool"><a href="ferramentas/{t["id"]}/">{E(t["name"])}</a><br><span class="meta">{E(t["vendor"])}</span></td>'
            f'<td>{E(p["name"])}</td><td class="price">{price_span(p["price_monthly_usd"])}{ann}{pu}</td>'
            f'<td class="lim">{E(p["limits_pt"])}</td><td>{badges}<br><span class="meta">{d_pt(t["checked"])}</span></td></tr>')
nplans = sum(len(t["plans"]) for t in tools)
cards = "".join(f'<a class="card" style="text-decoration:none;color:inherit" href="ferramentas/{t["id"]}/"><h3>{E(t["name"])}</h3><p>{E(t["summary_pt"])}</p><span class="badge">{E(t["type"])}</span></a>' for t in tools)
latest = "".join(f'<li><time>{d_pt(c["date"])}</time><h3>{E(c["title_pt"])}</h3><p>{E(c["detail_pt"])}</p></li>' for c in sorted(changes,key=lambda c:c["date"],reverse=True)[:3])
home = f"""<section class="hero"><h1>Quanto custa programar com IA <em>hoje</em>?</h1>
<p>Preços e limites do Cursor, Claude Code, Codex, Copilot, Gemini/Antigravity, Windsurf, Kiro e mais, lado a lado, em US$, R$, Kz e €. Verificados nas páginas oficiais.</p>
<p class="meta" style="margin-top:10px">{len(tools)} ferramentas · {nplans} planos · atualizado a {d_pt(meta["updated"])} · {fxline}</p></section>
<div class="controls"><input id="q" type="search" placeholder="Filtrar: ferramenta, plano, limite…" aria-label="Filtrar">
<select id="maxp" aria-label="Preço máximo"><option value="">Qualquer preço</option><option value="0">Só grátis</option><option value="10">até US$10</option><option value="20">até US$20</option><option value="40">até US$40</option><option value="100">até US$100</option></select>
<label class="chk"><input type="checkbox" id="freeonly"> plano grátis</label><label class="chk"><input type="checkbox" id="veronly"> só verificados</label>
{cur_switch()}<span class="meta" id="count"></span></div>
<div class="tablebox"><table id="cmp"><thead><tr><th data-sort="tool">Ferramenta</th><th data-sort="plan">Plano</th><th data-sort="price">Preço/mês</th><th>Limites e o que inclui</th><th>Estado</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
<p class="meta">{E(meta["disclaimer_pt"])} Viu um erro? <a href="mailto:{CORRECTION_EMAIL}?subject=Corre%C3%A7%C3%A3o%20Radar%20IA%20Dev">Envie uma correção</a>.</p>
{newsletter_block()}
<h2>Últimas mudanças</h2><ul class="changes">{latest}</ul><p><a href="mudancas/">Ver todas as mudanças →</a></p>
<h2 style="margin-top:36px">Ferramentas</h2><div class="grid">{cards}</div>"""
jsonld = json.dumps({"@context":"https://schema.org","@type":"WebSite","name":"Radar IA Dev","url":SITE_URL,"inLanguage":"pt"},ensure_ascii=False)
home += f'<script type="application/ld+json">{jsonld}</script>'
(OUT/"index.html").write_text(layout("Radar IA Dev — Preços do Cursor, Claude Code, Codex e Copilot em R$, Kz e €",
    "Compare preços e limites das ferramentas de IA para programar (Cursor, Claude Code, Codex, Copilot, Antigravity, Windsurf, Kiro) em reais, kwanzas e euros. Atualizado toda semana.", "", home, 0, ""))
pages.append("")
# ---- Tool pages
for t in tools:
    trs = "".join(f'<tr><td><strong>{E(p["name"])}</strong></td><td class="price">{price_span(p["price_monthly_usd"])}'
        + (f'<small>anual: <span data-usd="{p["price_annual_usd_per_month"]}">US$ {p["price_annual_usd_per_month"]}</span>/mês</small>' if p.get("price_annual_usd_per_month") else "")
        + ("<small>por utilizador</small>" if p.get("per_user") else "")
        + f'</td><td class="lim">{E(p["limits_pt"])}{("<br><span class=meta>"+E(p["verification_note"])+"</span>") if p.get("verification_note") else ""}</td>'
        + f'<td>{"<span class=\"badge ok\">verificado</span>" if p["verified"] else "<span class=\"badge no\">não verificado</span>"}</td></tr>' for p in t["plans"])
    tch = [c for c in changes if c.get("tool")==t["id"]]
    chh = ("<h2>Histórico de mudanças</h2><ul class='changes'>" + "".join(f'<li><time>{d_pt(c["date"])}</time><h3>{E(c["title_pt"])}</h3><p>{E(c["detail_pt"])}</p></li>' for c in tch) + "</ul>") if tch else "<p class='meta'>Ainda sem mudanças registadas desde o início do acompanhamento.</p>"
    srcs = [t["source_url"]] + t.get("extra_sources", [])
    paid = [p["price_monthly_usd"] for p in t["plans"] if p["price_monthly_usd"]]
    desc = f'Planos e preços do {t["name"]} em R$, Kz e €: ' + (f'a partir de US${min(paid):g}/mês. ' if paid else "") + t["free_tier_pt"]
    body = f"""<div class="crumbs"><a href="../../">Comparar</a> › {E(t["name"])}</div>
<section class="hero" style="padding-top:14px"><h1>{E(t["name"])}: preços e limites</h1><p>{E(t["summary_pt"])}</p>
<p class="meta" style="margin-top:8px">{E(t["vendor"])} · {E(t["type"])} · verificado a {d_pt(t["checked"])} · <a href="{E(t["website"])}" rel="nofollow noopener">site oficial</a></p></section>
<div class="controls">{cur_switch()}</div>
<div class="tablebox"><table class="plans"><thead><tr><th>Plano</th><th>Preço/mês</th><th>Limites e o que inclui</th><th>Estado</th></tr></thead><tbody>{trs}</tbody></table></div>
<div class="grid"><div class="card"><h3>🎁 Plano grátis</h3><p>{E(t["free_tier_pt"])}</p></div><div class="card"><h3>📝 Notas</h3><p>{E(t["notes_pt"])}</p></div></div>
{chh}<p class="meta">Fontes: {" · ".join(f'<a href="{E(s)}" rel="nofollow noopener">{E(s)}</a>' for s in srcs)}. {fxline}.<br>
Algo desatualizado? <a href="mailto:{CORRECTION_EMAIL}?subject=Corre%C3%A7%C3%A3o%3A%20{E(t["name"])}">Envie uma correção</a>.</p>{newsletter_block()}"""
    d = OUT/"ferramentas"/t["id"]; d.mkdir(parents=True)
    (d/"index.html").write_text(layout(f'{t["name"]}: preços e limites em R$, Kz e € — Radar IA Dev', desc, f'ferramentas/{t["id"]}/', body, 2))
    pages.append(f'ferramentas/{t["id"]}/')
# ---- Changes
names = {t["id"]: t["name"] for t in tools}
lis = "".join(f'<li id="{c["date"]}-{c.get("tool") or "geral"}"><time datetime="{c["date"]}">{d_pt(c["date"])}</time>'
    + (f' · <a href="../ferramentas/{c["tool"]}/">{E(names.get(c["tool"], c["tool"]))}</a>' if c.get("tool") else "")
    + f'<h3>{E(c["title_pt"])}</h3><p>{E(c["detail_pt"])}</p>'
    + (f'<p class="meta"><a href="{E(c["source"])}" rel="nofollow noopener">fonte</a></p>' if c.get("source") else "") + "</li>"
    for c in sorted(changes, key=lambda c: c["date"], reverse=True))
body = f"""<section class="hero"><h1>Mudanças</h1><p>Registo datado de cada alteração de preço, limite ou plano gratuito que detetamos. Verificamos as páginas oficiais toda semana.</p></section>
<ul class="changes">{lis}</ul><p class="meta">Também disponível em <a href="../data/changes.json">JSON</a>.</p>{newsletter_block()}"""
(OUT/"mudancas").mkdir(); (OUT/"mudancas/index.html").write_text(layout("Mudanças de preços e limites das IAs para programar — Radar IA Dev",
    "Histórico datado das mudanças de preços, limites e planos grátis do Cursor, Claude Code, Codex, Copilot e outras ferramentas de IA para programar.", "mudancas/", body, 1, "mudancas/"))
pages.append("mudancas/")
# ---- Sponsor
body = f"""<section class="hero"><h1>Anuncie no Radar IA Dev</h1><p>Chegue a programadores de língua portuguesa (Brasil, Angola, Moçambique, Portugal, Cabo Verde…) no momento em que estão a decidir que ferramenta de IA pagar.</p></section>
<div class="grid">
<div class="card"><h3>📬 Patrocinador da newsletter</h3><p>Bloco no topo da edição de segunda-feira: logótipo, até 80 palavras e 1 link. Um patrocinador por edição.</p><p class="meta">Preço: sob consulta (tabela de lançamento em breve)</p></div>
<div class="card"><h3>⭐ Ferramenta em destaque</h3><p>Destaque na tabela comparativa e na página da ferramenta, sempre identificado como "patrocinado". Os dados de preço nunca são alterados por patrocínio.</p><p class="meta">Preço: sob consulta</p></div>
<div class="card"><h3>🧭 Página de categoria</h3><p>Patrocínio exclusivo de uma página (ex.: "IA grátis para programar") durante um mês.</p><p class="meta">Preço: sob consulta</p></div></div>
<div class="card"><h3>Regras editoriais</h3><p>Preços e limites vêm sempre das páginas oficiais e são marcados como verificados ou não. Patrocinadores não podem pedir para alterar, esconder ou reordenar dados. Todo o conteúdo pago leva a etiqueta "patrocinado".</p>
<p><a class="btn" href="mailto:{SPONSOR_EMAIL}?subject=Patroc%C3%ADnio%20Radar%20IA%20Dev">Falar sobre patrocínio</a></p><p class="placeholder">⚠️ PLACEHOLDER: email de contacto ainda não configurado.</p></div>"""
(OUT/"anuncie").mkdir(); (OUT/"anuncie/index.html").write_text(layout("Anuncie aqui — Radar IA Dev",
    "Patrocine a newsletter e o comparador Radar IA Dev e chegue a programadores lusófonos que estão a escolher ferramentas de IA.", "anuncie/", body, 1, "anuncie/"))
pages.append("anuncie/")
# ---- 404, sitemap, robots
# O 404 é servido em qualquer caminho: usar <base> com o sub-caminho do site para os links relativos funcionarem.
from urllib.parse import urlparse
_base = urlparse(SITE_URL).path.rstrip("/") + "/"
_404 = layout("Página não encontrada — Radar IA Dev","Página não encontrada.","404.html",
    '<section class="hero"><h1>Página não encontrada</h1><p><a href="./">Voltar ao comparador</a></p></section>',0)
_404 = _404.replace('<meta charset="utf-8">', f'<meta charset="utf-8"><base href="{_base}"><meta name="robots" content="noindex">', 1)
(OUT/"404.html").write_text(_404)
today = datetime.date.today().isoformat()
(OUT/"sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    + "".join(f"<url><loc>{SITE_URL.rstrip('/')}/{p}</loc><lastmod>{today}</lastmod></url>" for p in pages) + "</urlset>")
(OUT/"robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL.rstrip('/')}/sitemap.xml\n")
(OUT/".nojekyll").write_text("")
print(f"Site gerado em {OUT}: {len(pages)} páginas, {len(tools)} ferramentas, {nplans} planos")
