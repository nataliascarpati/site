# Site de Natalia Scarpati

Site estático publicado pelo GitHub Pages em https://nataliascarpati.com.br.
Cada envio (push) para `main` gera e publica o site automaticamente.

## Onde fica cada coisa

| Pasta | O que tem |
|---|---|
| `conteudo/site.md` | Nome, frase de abertura, contatos, texto do Sobre |
| `conteudo/projetos/*.md` | Um arquivo por projeto. O nome do arquivo é o endereço (`mira.md` → `/mira/`) |
| `conteudo/projetos/_modelo.md` | Modelo para um projeto novo (arquivos com `_` são ignorados) |
| `img/`, `video/` | Fotos e vídeos já otimizados |
| `modelo/` | Estilo (CSS) e ícone |
| `ferramentas/` | Scripts de geração, preparação de fotos e importação do Cargo |
| `publico/` | Resultado gerado (não editar, não versionado) |

## Lançar um projeto novo

1. Preparar as fotos: `python3 ferramentas/preparar_fotos.py SLUG foto1.jpg foto2.jpg video.mov`
   O script grava em `img/SLUG/` e `video/SLUG/` e imprime as linhas de `midia:`.
2. Copiar `_modelo.md` para `conteudo/projetos/SLUG.md` e preencher.
   `ano` + `ordem` definem a posição no índice (ano mais recente primeiro; `ordem` 1 = primeiro do ano).
   `rascunho: sim` esconde o projeto; remover a linha para publicar.
3. Conferir: `python3 ferramentas/gerar_site.py` e abrir `publico/index.html`.
4. `git add -A && git commit -m "Novo projeto: Nome" && git push`. Em ~1 minuto está no ar.

## Campos de um projeto

`titulo`, `tipo`, `ano` são obrigatórios. `capa` é a foto do índice (fica recortada em 4:5).
Opcionais: `ordem`, `material`, `dimensoes`, `rascunho`, `endereco-antigo` (cria redirecionamento).
O texto em inglês vai entre `::: en` e `:::` e aparece como "English" recolhido.

## Saída do Cargo

As referências `cargo:` e `cargo-video:` apontam para os arquivos ainda hospedados no Cargo.
Antes de cancelar o Cargo, rodar uma vez **Actions → Importar fotos do Cargo → Run workflow**.
Ele baixa tudo para `img/` e `video/` e atualiza os arquivos de conteúdo.

## Domínio (Hostgator)

Na zona DNS de nataliascarpati.com.br:
- 4 registros **A** para `@`: 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
- 1 registro **CNAME** para `www` → `USUARIO.github.io`
Depois, no GitHub: Settings → Pages → Custom domain = `nataliascarpati.com.br` e marcar "Enforce HTTPS".
