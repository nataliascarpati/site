#!/usr/bin/env python3
"""Gera o site estático de Natalia Scarpati.

Lê   conteudo/site.md e conteudo/projetos/*.md
Gera publico/  (o que vai para o GitHub Pages)

Não depende de nenhuma biblioteca externa: roda com o Python que já vem no
computador ou no GitHub.

Uso:  python3 ferramentas/gerar_site.py
"""
import html
import os
import re
import shutil
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTEUDO = os.path.join(RAIZ, "conteudo")
MODELO = os.path.join(RAIZ, "modelo")
SAIDA = os.path.join(RAIZ, "publico")

FREIGHT = "https://freight.cargo.site"


# ---------------------------------------------------------------- leitura

def ler_md(caminho):
    """Lê um arquivo .md com cabeçalho simples entre linhas '---'."""
    with open(caminho, encoding="utf-8") as f:
        bruto = f.read()
    meta, corpo = {}, bruto
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", bruto, re.S)
    if m:
        cab, corpo = m.group(1), m.group(2)
        chave_lista = None
        for linha in cab.splitlines():
            if not linha.strip():
                continue
            item = re.match(r"^\s+-\s+(.*)$", linha)
            if item and chave_lista:
                meta[chave_lista].append(item.group(1).strip())
                continue
            k, _, v = linha.partition(":")
            k, v = k.strip(), v.strip()
            if v == "":
                meta[k] = []
                chave_lista = k
            else:
                meta[k] = v
                chave_lista = None
    pt, en = corpo, ""
    m = re.search(r"^::: en\n(.*?)\n:::\s*$", corpo, re.S | re.M)
    if m:
        en = m.group(1)
        pt = corpo[: m.start()]
    return meta, pt.strip(), en.strip()


def paragrafos(texto):
    blocos = [b.strip() for b in re.split(r"\n\s*\n", texto) if b.strip()]
    return "\n".join(f"<p>{html.escape(b).replace(chr(10), '<br>')}</p>" for b in blocos)


def resumo(texto, limite=155):
    t = re.sub(r"\s+", " ", texto).strip()
    if len(t) <= limite:
        return t
    return t[:limite].rsplit(" ", 1)[0] + "…"


# ---------------------------------------------------------------- mídia

def eh_video(ref):
    return ref.startswith("cargo-video:") or ref.lower().endswith((".mp4", ".mov", ".webm"))


def url_midia(ref, prefixo, largura=1800):
    """Converte a referência do .md em endereço de arquivo."""
    if ref.startswith("cargo-video:"):
        return f"{FREIGHT}/m/{ref.split(':', 1)[1]}"
    if ref.startswith("cargo:"):
        return f"{FREIGHT}/w/{largura}/q/80/i/{ref.split(':', 1)[1]}"
    return prefixo + ref


def url_absoluta(ref, dominio):
    if ref.startswith("cargo"):
        return url_midia(ref, "", 1200)
    return f"https://{dominio}/{ref}"


def versao_pequena(ref, prefixo):
    """Para fotos locais, usa a versão -900 gerada pelo importador, se existir."""
    if ref.startswith("cargo:"):
        return url_midia(ref, prefixo, 900)
    base, ext = os.path.splitext(ref)
    pequena = f"{base}-900{ext}"
    if os.path.exists(os.path.join(RAIZ, pequena)):
        return prefixo + pequena
    return None


def tag_imagem(ref, prefixo, alt, classe="", carregar="lazy", tamanhos="100vw"):
    grande = url_midia(ref, prefixo)
    pequena = versao_pequena(ref, prefixo)
    srcset = f' srcset="{pequena} 900w, {grande} 1800w" sizes="{tamanhos}"' if pequena else ""
    cls = f' class="{classe}"' if classe else ""
    return (f'<img{cls} src="{grande}"{srcset} alt="{html.escape(alt)}" '
            f'loading="{carregar}" decoding="async">')


def tag_midia(ref, prefixo, alt, carregar="lazy"):
    if eh_video(ref):
        return (f'<video src="{url_midia(ref, prefixo)}" autoplay muted loop playsinline '
                f'preload="metadata" aria-label="{html.escape(alt)}"></video>')
    return tag_imagem(ref, prefixo, alt, carregar=carregar,
                      tamanhos="(min-width: 900px) 60vw, 100vw")


# ---------------------------------------------------------------- moldura

def pagina(site, prefixo, titulo, descricao, corpo, canonico, imagem=None, atual=""):
    dominio = site["dominio"]
    titulo_completo = titulo if titulo == site["nome"] else f"{titulo} — {site['nome']}"
    og = f'<meta property="og:image" content="{imagem}">\n' if imagem else ""
    nav = []
    for chave, rotulo, href in (("projetos", "Projetos", f"{prefixo}./"),
                                ("sobre", "Sobre", f"{prefixo}sobre/")):
        marca = ' aria-current="page"' if chave == atual else ""
        nav.append(f'<a href="{href}"{marca}>{rotulo}</a>')
    nav.append(f'<a href="mailto:{site["email"]}">Contato</a>')
    logo = site.get("logo")
    if logo:
        marca = (f'<img class="logo" src="{url_midia(logo, prefixo, 800)}" '
                 f'alt="{html.escape(site["nome"])}" width="220" height="100">')
    else:
        marca = html.escape(site["nome"])
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(titulo_completo)}</title>
<meta name="description" content="{html.escape(descricao)}">
<link rel="canonical" href="https://{dominio}/{canonico}">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(titulo_completo)}">
<meta property="og:description" content="{html.escape(descricao)}">
<meta property="og:url" content="https://{dominio}/{canonico}">
{og}<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{prefixo}icone.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400;0,6..96,500;1,6..96,400&family=Hanken+Grotesk:wght@400;500&family=IBM+Plex+Mono:wght@400&display=swap">
<link rel="stylesheet" href="{prefixo}estilo.css">
</head>
<body>
<header class="topo">
  <a class="marca" href="{prefixo}./">{marca}</a>
  <nav class="menu" aria-label="Principal">{''.join(nav)}</nav>
</header>
<main>
{corpo}
</main>
<footer class="rodape">
  <p class="rodape-nome">{html.escape(site['nome'])}</p>
  <ul>
    <li><a href="mailto:{site['email']}">{site['email']}</a></li>
    <li><a href="https://www.instagram.com/{site['instagram']}" rel="noopener">Instagram @{site['instagram']}</a></li>
    <li><a href="https://www.linkedin.com/in/{site['linkedin']}" rel="noopener">LinkedIn</a></li>
  </ul>
  <p class="rodape-ano">© {date.today().year}</p>
</footer>
</body>
</html>
"""


def redirecionamento(destino_relativo, destino_absoluto):
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Redirecionando…</title>
<link rel="canonical" href="{destino_absoluto}">
<meta http-equiv="refresh" content="0; url={destino_relativo}">
</head><body><p><a href="{destino_relativo}">Continuar</a></p></body></html>
"""


def gravar(caminho_rel, conteudo):
    destino = os.path.join(SAIDA, caminho_rel)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        f.write(conteudo)


# ---------------------------------------------------------------- páginas

def montar():
    site, sobre_pt, sobre_en = ler_md(os.path.join(CONTEUDO, "site.md"))
    dominio = site["dominio"]

    projetos = []
    pasta = os.path.join(CONTEUDO, "projetos")
    for nome in os.listdir(pasta):
        if not nome.endswith(".md") or nome.startswith("_"):
            continue
        meta, pt, en = ler_md(os.path.join(pasta, nome))
        if meta.get("rascunho", "").lower() in ("sim", "true"):
            continue
        meta["slug"] = nome[:-3]
        meta["pt"], meta["en"] = pt, en
        meta.setdefault("midia", [])
        projetos.append(meta)
    projetos.sort(key=lambda p: (-int(p["ano"]), int(p.get("ordem", 99)), p["titulo"]))

    if os.path.exists(SAIDA):
        shutil.rmtree(SAIDA)
    os.makedirs(SAIDA)
    for arq in os.listdir(MODELO):
        shutil.copy(os.path.join(MODELO, arq), os.path.join(SAIDA, arq))
    for pasta_midia in ("img", "video"):
        origem = os.path.join(RAIZ, pasta_midia)
        if os.path.isdir(origem) and os.listdir(origem):
            shutil.copytree(origem, os.path.join(SAIDA, pasta_midia))

    # --- início
    pecas = []
    for n, p in enumerate(projetos):
        alt = f"{p['tipo']} {p['titulo']}, de Natalia Scarpati"
        destaque = p.get("destaque") or p["capa"]
        if eh_video(destaque):
            midia = (f'<video src="{url_midia(destaque, "")}" autoplay muted loop playsinline '
                     f'preload="metadata" aria-label="{html.escape(alt)}"></video>')
        else:
            midia = tag_imagem(destaque, "", alt, carregar="eager" if n < 6 else "lazy",
                               tamanhos="(min-width: 1100px) 33vw, 50vw")
        pecas.append(f"""<li class="peca">
  <a href="{p['slug']}/">
    <span class="peca-midia">{midia}</span>
    <span class="peca-legenda"><span class="peca-titulo">{html.escape(p['titulo'])}</span><span class="peca-tipo">{html.escape(p['tipo'])}</span></span>
  </a>
</li>""")

    corpo_inicio = f"""<h1 class="oculto">{html.escape(site['nome'])}: projetos</h1>
<ul class="mosaico">
{chr(10).join(pecas)}
</ul>"""
    gravar("index.html", pagina(site, "", site["nome"], site["descricao"], corpo_inicio, "",
                                url_absoluta(projetos[0]["capa"], dominio), "projetos"))

    # --- projetos
    for i, p in enumerate(projetos):
        pre = "../"
        midias = p["midia"] or [p["capa"]]
        figuras = []
        for n, r in enumerate(midias):
            alt = "{} {}, imagem {}".format(p["tipo"], p["titulo"], n + 1)
            figuras.append('<figure class="midia">{}</figure>'.format(
                tag_midia(r, pre, alt, "eager" if n == 0 else "lazy")))
        figuras = "\n".join(figuras)
        ficha = [f"<div><dt>Tipo</dt><dd>{html.escape(p['tipo'])}</dd></div>",
                 f"<div><dt>Ano</dt><dd>{p['ano']}</dd></div>"]
        if p.get("material"):
            ficha.append(f"<div><dt>Material</dt><dd>{html.escape(p['material'])}</dd></div>")
        if p.get("dimensoes"):
            ficha.append(f"<div><dt>Dimensões</dt><dd>{html.escape(p['dimensoes'])}</dd></div>")
        ingles = (f'<details class="ingles"><summary>English</summary>{paragrafos(p["en"])}</details>'
                  if p["en"] else "")
        ant = projetos[i - 1] if i > 0 else projetos[-1]
        prox = projetos[i + 1] if i + 1 < len(projetos) else projetos[0]
        corpo = f"""<article class="projeto">
  <div class="projeto-texto">
    <a class="voltar" href="../">← Todos os projetos</a>
    <h1>{html.escape(p['titulo'])}</h1>
    <dl class="ficha">{''.join(ficha)}</dl>
    <div class="texto">{paragrafos(p['pt'])}</div>
    {ingles}
  </div>
  <div class="projeto-midia">
{figuras}
  </div>
</article>
<nav class="vizinhos" aria-label="Outros projetos">
  <a href="../{ant['slug']}/"><span>Anterior</span>{html.escape(ant['titulo'])}</a>
  <a href="../{prox['slug']}/"><span>Próximo</span>{html.escape(prox['titulo'])}</a>
</nav>"""
        desc = f"{p['tipo']} {p['titulo']} ({p['ano']}), de Natalia Scarpati. {resumo(p['pt'], 110)}"
        gravar(f"{p['slug']}/index.html",
               pagina(site, pre, f"{p['tipo']} {p['titulo']}", desc, corpo, f"{p['slug']}/",
                      url_absoluta(p["capa"], dominio)))
        antigo = p.get("endereco-antigo")
        if antigo:
            gravar(f"{antigo}/index.html",
                   redirecionamento(f"../{p['slug']}/", f"https://{dominio}/{p['slug']}/"))

    # --- sobre
    fotos = site.get("fotos-sobre", [])
    galeria = "\n".join(
        f'<figure>{tag_imagem(r, "../", "Natalia Scarpati, exposição e ateliê", tamanhos="(min-width: 900px) 30vw, 50vw")}</figure>'
        for r in fotos)
    ingles = (f'<details class="ingles"><summary>English</summary>{paragrafos(sobre_en)}</details>'
              if sobre_en else "")
    corpo_sobre = f"""<article class="sobre">
  <div class="sobre-texto">
    <h1>Sobre</h1>
    <div class="texto">{paragrafos(sobre_pt)}</div>
    {ingles}
    <dl class="ficha contato">
      <div><dt>Email</dt><dd><a href="mailto:{site['email']}">{site['email']}</a></dd></div>
      <div><dt>Instagram</dt><dd><a href="https://www.instagram.com/{site['instagram']}" rel="noopener">@{site['instagram']}</a></dd></div>
      <div><dt>LinkedIn</dt><dd><a href="https://www.linkedin.com/in/{site['linkedin']}" rel="noopener">in/{site['linkedin']}</a></dd></div>
    </dl>
  </div>
  <div class="sobre-fotos">
{galeria}
  </div>
</article>"""
    gravar("sobre/index.html",
           pagina(site, "../", "Sobre", resumo(sobre_pt), corpo_sobre, "sobre/", None, "sobre"))

    # --- endereços antigos do Cargo
    for antigo in ("information", "contact-form"):
        gravar(f"{antigo}/index.html", redirecionamento("../sobre/", f"https://{dominio}/sobre/"))
    gravar("index/index.html", redirecionamento("../", f"https://{dominio}/"))

    # --- 404
    corpo_404 = """<section class="aviso">
  <h1>Esta página não existe mais.</h1>
  <p><a class="voltar" href="/">← Ver todos os projetos</a></p>
</section>"""
    gravar("404.html", pagina(site, "/", "Página não encontrada", site["descricao"], corpo_404, "404.html"))

    # --- arquivos de apoio
    urls = [""] + [f"{p['slug']}/" for p in projetos] + ["sobre/"]
    gravar("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "".join(f"  <url><loc>https://{dominio}/{u}</loc></url>\n" for u in urls)
           + "</urlset>\n")
    gravar("robots.txt", f"User-agent: *\nAllow: /\nSitemap: https://{dominio}/sitemap.xml\n")
    gravar("CNAME", dominio + "\n")
    gravar(".nojekyll", "")

    print(f"Site gerado em publico/ com {len(projetos)} projetos.")


if __name__ == "__main__":
    montar()
