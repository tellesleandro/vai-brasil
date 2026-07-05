#!/usr/bin/env python3
"""VAI BRASIL !!! — banner verde e amarelo em tela cheia no terminal.

Desenha, ocupando o terminal inteiro:

  - "VAI" numa linha e "BRASIL !!!" na outra, em letras gigantes tecidas
    com simbolos UTF-8, alternando verde e amarelo;
  - duas bandeiras do Brasil, uma de cada lado do "VAI";
  - um fundo de estrelinhas esparsas.

Uso:

    python3 vai-brasil.py

O banner fica na tela (cursor escondido) para voce tirar um print;
aperte Enter (ou Ctrl+C) para sair e restaurar o terminal.

O desenho se adapta ao tamanho do terminal: quanto maior a janela,
maiores as letras. Para o efeito completo, use o terminal em tela cheia.

Guia rapido para modificar:

  - Trocar o texto ......... lista `texts` no inicio de main()
  - Trocar os simbolos ..... constantes TEX e SPARKS
  - Trocar as cores ........ constantes G/g/Y/y/BL/W (codigos ANSI)
  - Densidade de estrelas .. SPARK_DENSITY
  - Novas letras ........... dicionario FONT (desenhe com '#' e espacos)
  - Circulo achatado? ...... ajuste CELL_ASPECT para a sua fonte
"""
import random
import shutil
import sys

# ---------------------------------------------------------------------------
# Cores (codigos de escape ANSI)
# ---------------------------------------------------------------------------
# "1;" = versao brilhante. Referencia: 31 vermelho, 32 verde, 33 amarelo,
# 34 azul, 35 magenta, 36 ciano, 37 branco.
G = "\033[1;32m"   # verde brilhante  (letras)
g = "\033[32m"     # verde normal     (estrelinhas)
Y = "\033[1;33m"   # amarelo brilhante(letras)
y = "\033[33m"     # amarelo normal   (estrelinhas)
BL = "\033[1;34m"  # azul   (circulo da bandeira)
W = "\033[1;37m"   # branco (faixa da bandeira)
R = "\033[0m"      # reset: volta a cor padrao do terminal

# ---------------------------------------------------------------------------
# Simbolos
# ---------------------------------------------------------------------------
# Textura que preenche o corpo das letras. O simbolo de cada celula e
# escolhido por (linha + coluna) % len(TEX), o que cria um padrao que
# "corre" na diagonal. Qualquer string de simbolos de largura 1 funciona.
TEX = "★✦❋●◆✸✿☀"

# Estrelinhas esparsas do fundo e suas cores possiveis.
SPARKS = "✦✧⋆·˚+*'✺"
SPARK_COLORS = (G, g, Y, y)
SPARK_DENSITY = 0.02  # fracao das celulas do fundo que viram estrelinha

# ---------------------------------------------------------------------------
# Fonte
# ---------------------------------------------------------------------------
# Cada letra e uma matriz de 7 linhas onde '#' = tinta e ' ' = vazio.
# As larguras podem variar de letra para letra. Para suportar outra letra,
# basta adicionar uma entrada aqui seguindo o mesmo formato.
FONT = {
    "V": ["#     #", "#     #", "#     #", " #   # ", " #   # ", "  # #  ", "   #   "],
    "A": ["   #   ", "  # #  ", " #   # ", "#######", "#     #", "#     #", "#     #"],
    "I": ["#######", "   #   ", "   #   ", "   #   ", "   #   ", "   #   ", "#######"],
    "B": ["###### ", "#     #", "#     #", "###### ", "#     #", "#     #", "###### "],
    "R": ["###### ", "#     #", "#     #", "###### ", "#   #  ", "#    # ", "#     #"],
    "S": [" ##### ", "#     #", "#      ", " ##### ", "      #", "#     #", " ##### "],
    "L": ["#      ", "#      ", "#      ", "#      ", "#      ", "#      ", "#######"],
    "!": ["##", "##", "##", "##", "##", "  ", "##"],
    " ": ["   "] * 7,
}
FONT_H = 7  # altura de todas as letras, em celulas da escala base
GAP = 2     # espaco entre letras, em celulas da escala base

# Proporcao visual das celulas do terminal (altura / largura do caractere).
# Usada para que o circulo da bandeira saia redondo e nao oval. Fontes
# monoespacadas comuns ficam entre 2.0 e 2.4; ajuste se o circulo sair
# achatado (aumente) ou alongado (diminua).
CELL_ASPECT = 2.2


def text_width(text):
    """Largura do texto na escala base (sem ampliacao)."""
    return sum(len(FONT[c][0]) for c in text) + GAP * (len(text) - 1)


def stamp(grid, text, top, sx, sy, ci):
    """Desenha `text` na grade, ampliado e centralizado na horizontal.

    Cada celula '#' da fonte vira um bloco de sx (largura) x sy (altura)
    celulas reais, preenchidas com a textura TEX. As letras alternam
    verde/amarelo; `ci` e o contador dessa alternancia, devolvido no final
    para que a proxima linha de texto continue a sequencia de cores.
    """
    lines = len(grid)
    cols = len(grid[0])
    left = max(0, (cols - text_width(text) * sx) // 2)
    x = left  # coluna (ja ampliada) onde comeca a proxima letra
    for ch in text:
        glyph = FONT[ch]
        color = ""
        if ch != " ":
            color = G if ci % 2 == 0 else Y
            ci += 1
        for gi, row in enumerate(glyph):
            for gj, cell in enumerate(row):
                if cell != "#":
                    continue
                # amplia a celula da fonte para um bloco sx x sy
                for dy in range(sy):
                    gy = top + gi * sy + dy
                    if not 0 <= gy < lines:
                        continue
                    for dx in range(sx):
                        gx = x + gj * sx + dx
                        if 0 <= gx < cols:
                            # (gy + gx) faz a textura variar na diagonal
                            grid[gy][gx] = (TEX[(gy + gx) % len(TEX)], color)
        x += (len(glyph[0]) + GAP) * sx
    return ci


def stamp_flag(grid, top, left, width, height):
    """Desenha uma bandeira do Brasil de `width` x `height` celulas.

    Em vez de ampliar uma arte pronta (que ficaria pixelada), cada celula
    e classificada geometricamente:

      - losango:  |u| + |v| <= 0.88, com u e v normalizados em -1..1
                  (0.88 controla o quanto as pontas chegam na borda);
      - circulo:  dx^2 + dy^2 <= raio^2, com dy multiplicado por
                  CELL_ASPECT para compensar celulas mais altas que largas
                  (0.26 abaixo controla o tamanho do circulo);
      - faixa:    banda em torno de uma parabola dentro do circulo,
                  lembrando a faixa "Ordem e Progresso".
    """
    lines = len(grid)
    cols = len(grid[0])
    radius = height * CELL_ASPECT * 0.26  # raio do circulo, em "pixels"
    for r_ in range(height):
        for c_ in range(width):
            # coordenadas normalizadas (-1..1), para o losango
            u = (c_ + 0.5 - width / 2) / (width / 2)
            v = (r_ + 0.5 - height / 2) / (height / 2)
            # coordenadas em "pixels" visuais, para o circulo e a faixa
            dx = c_ + 0.5 - width / 2
            dy = (r_ + 0.5 - height / 2) * CELL_ASPECT
            color = G
            if abs(u) + abs(v) <= 0.88:
                color = Y
            if dx * dx + dy * dy <= radius * radius:
                color = BL
                # parabola levemente deslocada para cima; a banda em volta
                # dela (grossura ~13% do raio) vira a faixa branca
                arc = -0.18 * radius + 0.25 * (dx * dx) / radius
                if abs(dy - arc) <= max(1.1, 0.13 * radius):
                    color = W
            gy, gx = top + r_, left + c_
            if 0 <= gy < lines and 0 <= gx < cols:
                grid[gy][gx] = ("█", color)


def compress(row):
    """Converte uma linha de celulas (char, cor) em string pronta para
    imprimir, emitindo o codigo ANSI so quando a cor muda (menos bytes)."""
    out, cur = [], None
    for char, color in row:
        if color != cur:
            out.append(color)
            cur = color
        out.append(char)
    return "".join(out) + R


def main():
    cols, lines = shutil.get_terminal_size()

    # As linhas do banner. Se mudar o texto, garanta que todas as letras
    # existem em FONT (so ha as necessarias para "VAI BRASIL !!!").
    texts = ["VAI", "BRASIL !!!"]

    # Escala vertical: os 2 blocos de FONT_H linhas + folga devem caber
    # na altura do terminal.
    sy = max(1, (lines - 4) // (FONT_H * 2 + 1))
    gap = max(2, sy)  # linhas em branco entre "VAI" e "BRASIL !!!"
    total_h = FONT_H * sy * 2 + gap
    top = max(0, (lines - total_h) // 2)

    # A grade representa a tela: cada celula e um par (caractere, cor).
    # Tudo e desenhado nela primeiro e impresso de uma vez no final.
    grid = [[(" ", "") for _ in range(cols)] for _ in range(lines)]

    # Fundo: ceu estrelado aleatorio (cada execucao sai diferente).
    for r in range(lines):
        for c in range(cols):
            if random.random() < SPARK_DENSITY:
                grid[r][c] = (random.choice(SPARKS), random.choice(SPARK_COLORS))

    # Escala horizontal unica, definida pela linha mais larga: "BRASIL !!!"
    # ocupa a largura toda e "VAI" usa letras do mesmo tamanho, centralizado.
    sx = max(1, (cols - 2) // max(text_width(t) for t in texts))
    ci = 0  # contador da alternancia verde/amarelo, continuo entre as linhas
    for i, t in enumerate(texts):
        row = top + i * (FONT_H * sy + gap)
        ci = stamp(grid, t, row, sx, sy, ci)

    # Bandeiras do Brasil de cada lado do "VAI", se houver espaco sobrando.
    vai_w = text_width(texts[0]) * sx
    side = (cols - vai_w) // 2          # espaco livre de cada lado
    flag_h = FONT_H * sy - 2 * sy       # um pouco menor que o bloco do VAI
    flag_w = int(flag_h * (10 / 7) * CELL_ASPECT)  # proporcao real 10:7
    if side >= flag_w + 4 and flag_h >= 5:
        flag_top = top + (FONT_H * sy - flag_h) // 2  # centraliza na altura
        margin = (side - flag_w) // 2                 # centraliza no vao
        stamp_flag(grid, flag_top, margin, flag_w, flag_h)
        stamp_flag(grid, flag_top, cols - side + margin, flag_w, flag_h)

    # Impressao: limpa a tela (\033[2J), move o cursor para o canto
    # (\033[H) e o esconde (\033[?25l). Sem "\n" na ultima linha para a
    # tela nao rolar.
    sys.stdout.write("\033[2J\033[H\033[?25l")
    sys.stdout.write("\n".join(compress(row) for row in grid))
    sys.stdout.flush()

    # Espera Enter com o banner na tela — hora de tirar o print.
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        # Restaura o terminal: cursor visivel, cores normais, tela limpa.
        sys.stdout.write("\033[?25h" + R + "\033[2J\033[H")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
