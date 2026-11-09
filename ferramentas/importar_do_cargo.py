#!/usr/bin/env python3
"""Baixa do Cargo todas as fotos e vídeos citados nos arquivos de conteúdo,
guarda cópias no próprio site (img/ e video/) e troca as referências
'cargo:' e 'cargo-video:' pelos arquivos locais.

Roda uma única vez, antes de cancelar o Cargo, pelo GitHub
(Actions > "Importar fotos do Cargo"). Pode ser repetido sem problema:
referências já importadas são ignoradas.
"""
import glob
import os
import re
import sys
import tempfile
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preparar_fotos import RAIZ, salvar_foto, salvar_video  # noqa: E402

FREIGHT = "https://freight.cargo.site"
REF = re.compile(r"\b(cargo(?:-video)?):([A-Z]\d+)/(\S+)")


def baixar(url, destino):
    req = urllib.request.Request(url, headers={"User-Agent": "nataliascarpati-site-import"})
    with urllib.request.urlopen(req, timeout=120) as r, open(destino, "wb") as f:
        f.write(r.read())


def main():
    arquivos = glob.glob(os.path.join(RAIZ, "conteudo", "*.md")) + \
        glob.glob(os.path.join(RAIZ, "conteudo", "projetos", "*.md"))
    feitos = {}
    falhas = []
    with tempfile.TemporaryDirectory() as tmp:
        for arq in sorted(arquivos):
            nome = os.path.basename(arq)[:-3]
            slug = "sobre" if nome == "site" else nome
            with open(arq, encoding="utf-8") as f:
                texto = f.read()
            contador = [0]

            def trocar(m):
                tipo, hash_, arquivo = m.groups()
                chave = f"{tipo}:{hash_}"
                if chave in feitos:
                    return feitos[chave]
                contador[0] += 1
                base = f"{slug}/{contador[0]:02d}"
                local = os.path.join(tmp, f"{hash_}_{arquivo}")
                try:
                    if tipo == "cargo-video":
                        baixar(f"{FREIGHT}/m/{hash_}/{arquivo}", local)
                        novo = salvar_video(local, f"video/{base}")
                    else:
                        baixar(f"{FREIGHT}/w/2400/q/90/i/{hash_}/{arquivo}", local)
                        novo = salvar_foto(local, f"img/{base}")
                except Exception as e:  # mantém a referência antiga se falhar
                    falhas.append(f"{nome}: {arquivo} ({e})")
                    return m.group(0)
                feitos[chave] = novo
                print("ok", novo)
                return novo

            # A logo fica em PNG transparente, sem margens sobrando.
            m_logo = re.search(r"^logo: cargo:([A-Z]\d+)/(\S+)$", texto, re.M)
            if m_logo:
                hash_, arquivo = m_logo.groups()
                local = os.path.join(tmp, "logo_" + arquivo)
                baixar(f"{FREIGHT}/w/1600/i/{hash_}/{arquivo}", local)
                from PIL import Image
                with Image.open(local) as im:
                    im = im.convert("RGBA")
                    alfa = im.getchannel("A")
                    if alfa.getextrema() == (255, 255):  # fundo branco: recorta pelo desenho
                        from PIL import ImageOps
                        caixa = ImageOps.invert(im.convert("L")).point(lambda v: 255 if v > 20 else 0).getbbox()
                    else:
                        caixa = alfa.getbbox()
                    im = im.crop(caixa)
                    im.thumbnail((900, 900), Image.LANCZOS)
                    im.save(os.path.join(RAIZ, "img", "logo.png"), optimize=True)
                texto = texto.replace(m_logo.group(0), "logo: img/logo.png")
                with open(arq, "w", encoding="utf-8") as f:
                    f.write(texto)
                print("ok img/logo.png")

            novo_texto = REF.sub(trocar, texto)
            if novo_texto != texto:
                with open(arq, "w", encoding="utf-8") as f:
                    f.write(novo_texto)
    if falhas:
        print("\nNão foi possível baixar:")
        print("\n".join(falhas))
        sys.exit(1)
    print(f"\n{len(feitos)} arquivos importados.")


if __name__ == "__main__":
    main()
