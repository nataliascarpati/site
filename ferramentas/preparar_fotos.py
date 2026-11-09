#!/usr/bin/env python3
"""Prepara fotos e vídeos de um projeto para o site.

    python3 ferramentas/preparar_fotos.py SLUG foto1.jpg foto2.png video.mov ...

Para cada foto grava img/SLUG/NN.jpg (até 2000 px) e img/SLUG/NN-900.jpg.
Para cada vídeo grava video/SLUG/NN.mp4 (H.264, sem som, até 1280 px).
Imprime as linhas prontas para colar em 'midia:' no arquivo do projeto.
Precisa de Pillow (pip install pillow) e, para vídeos, ffmpeg.
"""
import os
import subprocess
import sys

from PIL import Image, ImageOps

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_EXT = (".mov", ".mp4", ".m4v", ".webm", ".avi")


def salvar_foto(origem, destino_base):
    """destino_base sem extensão, relativo à raiz. Devolve o caminho principal."""
    with Image.open(origem) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            fundo = Image.new("RGB", im.size, (255, 255, 255))
            fundo.paste(im, mask=im.split()[-1])
            im = fundo
        else:
            im = im.convert("RGB")
        os.makedirs(os.path.join(RAIZ, os.path.dirname(destino_base)), exist_ok=True)
        for lado, sufixo, qualidade in ((2000, "", 84), (900, "-900", 80)):
            copia = im.copy()
            copia.thumbnail((lado, lado), Image.LANCZOS)
            copia.save(os.path.join(RAIZ, destino_base + sufixo + ".jpg"), "JPEG",
                       quality=qualidade, optimize=True, progressive=True)
    return destino_base + ".jpg"


def salvar_video(origem, destino_base):
    os.makedirs(os.path.join(RAIZ, os.path.dirname(destino_base)), exist_ok=True)
    saida = destino_base + ".mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", origem,
        "-vf", "scale='min(1280,iw)':-2", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an",
        os.path.join(RAIZ, saida)], check=True)
    return saida


def proximo_numero(slug):
    usados = set()
    for pasta in ("img", "video"):
        p = os.path.join(RAIZ, pasta, slug)
        if os.path.isdir(p):
            for n in os.listdir(p):
                if n[:2].isdigit():
                    usados.add(int(n[:2]))
    return max(usados, default=0) + 1


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    slug, arquivos = sys.argv[1], sys.argv[2:]
    n = proximo_numero(slug)
    linhas = []
    for arq in arquivos:
        if arq.lower().endswith(VIDEO_EXT):
            linhas.append(salvar_video(arq, f"video/{slug}/{n:02d}"))
        else:
            linhas.append(salvar_foto(arq, f"img/{slug}/{n:02d}"))
        n += 1
    print("midia:")
    for l in linhas:
        print(f"  - {l}")


if __name__ == "__main__":
    main()
