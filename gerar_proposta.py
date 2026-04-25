import os
import math, io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib import colors as rlcolors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader
from pypdf import PdfWriter, PdfReader

W, H = A4
TEMPLATE = os.path.join(os.path.dirname(__file__), "template.pdf")

# Fonte Carlito (substituta Montserrat)
pdfmetrics.registerFont(TTFont("Mont",     "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Mont-Bold","/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf"))

AZ="#11104E"; AM="#FCDB00"; BRN="#FFFFFF"; VD="#1B7A34"
VM="#C62828"; GR="#F4F4F4"; TX="#212121"; TX2="#555555"; CLAR="#E8EDF8"
TOP_H=28.0; BOT_H=29.0; TRI_TOP_W=96.0; TRI_BOT_W=116.0
M=34; Y0=H-TOP_H-20

def h2r(h):
    h=h.lstrip('#')
    return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))
def sf(c,col): r,g,b=h2r(col); c.setFillColorRGB(r,g,b)
def ss(c,col): r,g,b=h2r(col); c.setStrokeColorRGB(r,g,b)

def brl(v):
    return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

def num(v):
    """Formata número sem R$ prefixo"""
    return f"{float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

def txt(c, text, x, y, sz=10, col=AZ, bold=False, align="left"):
    c.saveState(); sf(c,col)
    c.setFont("Mont-Bold" if bold else "Mont", sz)
    if align=="center": c.drawCentredString(x,y,text)
    elif align=="right": c.drawRightString(x,y,text)
    else: c.drawString(x,y,text)
    c.restoreState()

def lnh(c,x1,y,x2,col=AM,lw=2.5):
    c.saveState(); ss(c,col); c.setLineWidth(lw)
    c.line(x1,y,x2,y); c.restoreState()

def rbox(c,x,y,w,h,r=8,fc=BRN,sc=None,lw=0.8):
    c.saveState(); sf(c,fc)
    if sc: ss(c,sc); c.setLineWidth(lw); c.roundRect(x,y,w,h,r,fill=1,stroke=1)
    else: c.roundRect(x,y,w,h,r,fill=1,stroke=0)
    c.restoreState()

def make_overlay(draw_fn):
    buf=io.BytesIO()
    c=rl_canvas.Canvas(buf,pagesize=A4)
    draw_fn(c); c.save(); buf.seek(0)
    return PdfReader(buf).pages[0]

# ═══════════════════════════════════════════════════════════════════════════
# OVERLAY PÁG 1 — Capa
# ═══════════════════════════════════════════════════════════════════════════
def overlay_capa(dados):
    def draw(c):
        txt(c, dados['nome'],   33.6, 140, 18, AM, True,  "left")
        txt(c, dados['cidade'], 33.6, 118, 13, BRN, False, "left")
    return make_overlay(draw)

# ═══════════════════════════════════════════════════════════════════════════
# OVERLAY PÁG 4 — Equipamentos
# Posições exatas (pdfplumber):
#   Badge "Módulos"  centro_x=154, badge_y_top=505.6
#   Badge "Inversor" centro_x=432, badge_y_top=505.6
#   Badge kWh: "kWh/mês" começa em x=285.9, y_pt=309.9
#              badge ocupa aprox x=130 até x=470
# ═══════════════════════════════════════════════════════════════════════════
def overlay_equipamentos(dados):
    def draw(c):
        # ── Specs MÓDULOS — coluna esquerda, centro x=154 ─────────────────
        # Posicionado abaixo da imagem do painel (badge Módulos em y=505.6)
        # Imagens ocupam aprox 120pt de altura → specs em y≈380-390
        spec_mod = f"{dados['qtd_pai']} Modulos {dados['marca_pai']} {dados['wp_pai']}W"
        txt(c, spec_mod, 154, 460, 16, AZ, True, "center")

        # ── Specs INVERSOR — coluna direita, centro x=432 ─────────────────
        tipo = dados.get('tipo_inv','Inversor')
        spec_inv = f"{dados['qtd_inv']} {tipo} {dados['marca_inv']} {dados['kw_inv']}kW"
        txt(c, spec_inv, 432, 460, 16, AZ, True, "center")

        # ── Valor kWh/mês ─────────────────────────────────────────────────
        # "kWh/mês" está em x0=285.9, y_pt=309.9
        # Apenas o NÚMERO, alinhado à direita encostado no "kWh/mês"
        # Badge de x≈130 até x≈470; número no espaço antes de x=283
        txt(c, str(dados["geracao"]), 265, 295.0, 20, AM, True, "right")

    return make_overlay(draw)

# ═══════════════════════════════════════════════════════════════════════════
# OVERLAY PÁG 7 — Investimento
# Posições exatas (pdfplumber):
#   "R$"   x0=182.2 x1=216.4  y_pt=689.5
#   "À"    x0=332.4            y_pt=689.5
#   "R$:"  x0=419.9 x1=444.4  y_pt=401.0
# ═══════════════════════════════════════════════════════════════════════════
def overlay_investimento(dados):
    def draw(c):
        # ── Valor à vista — só o número entre "R$" e "À vista" ───────────
        # Espaço: x=218 até x=330 → centro=274, y=689.5
        val_str = num(dados['inv'])
        txt(c, val_str, 274, 670.0, 24, BRN, True, "center")

        # ── Parcela 18x — só o número após "de R$:" (x1=444.4) ───────────
        # Sem "R$" pois já está no texto original
        parc_str = num(dados['parcela'])
        txt(c, parc_str, 448, 391.5, 15, "#000000", True, "left")

    return make_overlay(draw)

# ═══════════════════════════════════════════════════════════════════════════
# GRÁFICO — Retorno acumulado (matplotlib)
# ═══════════════════════════════════════════════════════════════════════════
def build_grafico_retorno(dados, acum):
    fig, ax = plt.subplots(figsize=(8.8, 3.8))
    fig.patch.set_facecolor("#F0F3FB")
    ax.set_facecolor("#F0F3FB")

    inv_val = dados['inv']
    anos_p  = list(range(0, 26))
    vals    = [0] + acum
    max_val = max(acum[-1], inv_val * 1.1)

    # Área prejuízo
    ax.fill_between(anos_p, vals, inv_val,
        where=[v < inv_val for v in vals],
        color="#C62828", alpha=0.10)
    # Área lucro
    ax.fill_between(anos_p, vals, inv_val,
        where=[v >= inv_val for v in vals],
        color="#1B7A34", alpha=0.12)

    # Linha investimento
    ax.axhline(inv_val, color="#C62828", linewidth=1.8,
               linestyle="--", label=f"Investimento ({brl(inv_val)})", zorder=3)

    # Linha acumulado
    ax.plot(anos_p, vals, color="#11104E", linewidth=2.8,
            zorder=4, label="Economia acumulada")

    # Payback
    pb_a = dados['pb'] / 12
    pb_x = pb_a
    ax.axvline(pb_x, color="#1B7A34", linewidth=1.4, linestyle=":", alpha=0.9)
    ax.scatter([pb_x], [inv_val], color="#1B7A34", s=60, zorder=6)
    ax.annotate(f"Payback\n{pb_a:.1f} anos",
        xy=(pb_x, inv_val),
        xytext=(pb_x + 1.5, inv_val + max_val * 0.07),
        fontsize=7.5, color="#1B7A34", fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="#1B7A34", lw=1.2))

    # Ponto 25 anos
    ax.scatter([25], [acum[-1]], color="#11104E", s=60, zorder=6)
    ax.annotate(f"  {brl(acum[-1])}",
        xy=(25, acum[-1]),
        xytext=(20, acum[-1] - max_val * 0.12),
        fontsize=7.5, color="#11104E", fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="#11104E", lw=1.2))

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"R$ {x/1000:.0f}k"))
    ax.set_xlabel("Ano", fontsize=8.5, color="#444444")
    ax.set_ylabel("Economia Acumulada (R$)", fontsize=8.5, color="#444444")
    ax.legend(fontsize=8, loc="upper left", framealpha=0.85)
    ax.grid(axis="y", alpha=0.2, linestyle="--", color="#AAAAAA")
    ax.set_xlim(0, 25)
    ax.tick_params(labelsize=8)
    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout(pad=0.4)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160,
                bbox_inches="tight", facecolor="#F0F3FB")
    plt.close(fig)
    buf.seek(0)
    return buf

# ═══════════════════════════════════════════════════════════════════════════
# PÁG 5 — ANÁLISE FINANCEIRA
# ═══════════════════════════════════════════════════════════════════════════
def build_analise(dados, acum):
    buf = io.BytesIO()
    c   = rl_canvas.Canvas(buf, pagesize=A4)
    y   = Y0

    # Título
    txt(c, "ANALISE FINANCEIRA", W/2, y, 18, AZ, True, "center")
    lnh(c, W/2-100, y-7, W/2+100, AM, 2)
    txt(c, f"Projecao de 25 anos  |  {dados['nome']}  |  {dados['cidade']}",
        W/2, y-18, 8.5, TX2, False, "center")
    y -= 36

    # ── 5 KPI Cards ────────────────────────────────────────────────────────
    kpis = [
        ("Investimento Total", brl(dados['inv'])),
        ("Economia Mensal",    brl(dados['eco_mes'])),
        ("Payback",            f"{dados['pb']} meses"),
        ("Lucro em 25 Anos",   brl(dados['roi'])),
        ("TIR Mensal",         f"{dados['tir']}% a.m."),
    ]
    cw = (W - 2*M - 16) / 5
    ch = 66
    xk = M
    for lb, val in kpis:
        rbox(c, xk, y-ch, cw, ch, 7, CLAR)
        sf(c, AZ); c.roundRect(xk, y-4.5, cw, 4.5, 3, fill=1, stroke=0)
        txt(c, lb,  xk+cw/2, y-18, 7,   TX2, False, "center")
        fsz = 10 if len(val) < 14 else 8.5
        txt(c, val, xk+cw/2, y-40, fsz, AZ,  True,  "center")
        xk += cw + 4

    txt(c,
        "* Tarifa Coelba R$ 0,92/kWh | Reajuste 5% a.a. | "
        "Degradacao 0,5% a.a. | Fio B incluido (Lei 14.300/2022)",
        W/2, y-ch-10, 6.2, "#999999", False, "center")
    y -= ch + 22

    # ── Gráfico matplotlib ─────────────────────────────────────────────────
    gh = 188
    rbox(c, M-4, y-gh-8, W-2*M+8, gh+16, 10, "#F0F3FB", "#D0D8EE", 0.5)
    txt(c, "Projecao de Retorno Acumulado em 25 Anos",
        W/2, y-12, 10, AZ, True, "center")
    lnh(c, M+30, y-18, W-M-30, AM, 1.5)

    g_buf = build_grafico_retorno(dados, acum)
    img   = ImageReader(g_buf)
    c.drawImage(img, M+2, y-gh-2,
                width=W-2*M-4, height=gh-22,
                preserveAspectRatio=True, mask="auto")
    y -= gh + 20

    # ── Tabela resumo ───────────────────────────────────────────────────────
    txt(c, "Resumo por Periodo", M, y-2, 9.5, AZ, True)
    lnh(c, M, y-7, M+148, AM, 2)
    y -= 18

    inv_val = dados['inv']
    tdata = [["Periodo", "Eco. Anual", "Eco. Acumulada", "Saldo"]]
    for p in [1, 2, 5, 10, 15, 20, 25]:
        eco_a = dados['eco_mes'] * 12 * (1.05**(p-1))
        ac_p  = acum[p-1]
        s     = ac_p - inv_val
        tdata.append([
            f"Ano {p}", brl(eco_a), brl(ac_p),
            ("+ " if s >= 0 else "") + brl(abs(s))
        ])

    cws = [(W-2*M)*v for v in [0.17, 0.24, 0.28, 0.31]]
    tbl = Table(tdata, colWidths=cws)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0), rlcolors.HexColor(AZ)),
        ("TEXTCOLOR",      (0,0), (-1,0), rlcolors.white),
        ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,-1), 7.5),
        ("ALIGN",          (0,0), (-1,-1), "CENTER"),
        ("VALIGN",         (0,0), (-1,-1), "MIDDLE"),
        ("ROWHEIGHT",      (0,0), (-1,-1), 14),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [rlcolors.HexColor(GR), rlcolors.white]),
        ("GRID",           (0,0), (-1,-1), 0.25, rlcolors.HexColor("#CCCCCC")),
        ("BACKGROUND",     (0,2), (-1,2), rlcolors.HexColor("#FFFDE7")),
    ]))
    _, th = tbl.wrapOn(c, sum(cws), 300)
    tbl.drawOn(c, M, y-th)

    c.save(); buf.seek(0)
    return PdfReader(buf).pages[0]

# ═══════════════════════════════════════════════════════════════════════════
# PÁG 6 — FIO B
# ═══════════════════════════════════════════════════════════════════════════
def build_fiob(dados, acum):
    buf = io.BytesIO()
    c   = rl_canvas.Canvas(buf, pagesize=A4)
    y   = Y0

    txt(c, "PROJECAO FIO B (GDII)", W/2, y, 18, AZ, True, "center")
    lnh(c, W/2-110, y-7, W/2+110, AM, 2)
    txt(c, "Lei 14.300/2022 - Marco Legal da Micro e Minigeracao Distribuida",
        W/2, y-18, 8.5, TX2, False, "center")
    y -= 36

    # Box explicativo
    rbox(c, M, y-82, W-2*M, 78, 8, "#EDF0FA", AZ, 0.8)
    sf(c, AM); c.rect(M, y-82, 5, 78, fill=1, stroke=0)
    txt(c, "O que e o Fio B e como impacta sua economia?", M+12, y-16, 9.5, AZ, True)
    for i, p in enumerate([
        "A Lei 14.300/2022 estabelece que sistemas instalados apos jan/2023 passam a pagar",
        "progressivamente o encargo de uso da rede de distribuicao (Fio B / TUSD-FP).",
        "O desconto comeca em 100% no 1o ano e reduz 20% ao ano, encerrando no 6o ano.",
        f"Na Bahia (Coelba), o Fio B representa aprox. R$ 0,26/kWh da tarifa total.",
        f"Mesmo com o encargo, seu sistema garante lucro de {brl(dados['roi'])} em 25 anos.",
    ]):
        txt(c, p, M+12, y-30-i*9, 7.8, TX)
    y -= 90

    # Tabela Fio B
    txt(c, "Detalhamento Anual - Primeiros 10 Anos", M, y-2, 9, AZ, True)
    lnh(c, M, y-7, M+200, AM, 2)
    y -= 18

    FIO_B = {1:1.0, 2:0.8, 3:0.6, 4:0.4, 5:0.2}
    ftab = [["Ano","Ano\nOp.","Desconto\nFio B",
             "Encargo\n(R$/mes)","Eco. Liquida\n(R$/mes)",
             "% Eco.\nPreservada","Status"]]
    for i in range(10):
        ao   = i+1
        dv   = FIO_B.get(ao, 0)
        gm   = dados['geracao'] * (0.995**i)
        fiob = gm * 0.26 * (1-dv) * (1.05**i)
        eco_m= gm * 0.92 * (1.05**i) / 12 - fiob
        pct  = eco_m / (gm*0.92*(1.05**i)/12) * 100 if gm > 0 else 100
        ftab.append([
            str(2025+i), str(ao), f"{int(dv*100)}%",
            f"R$ {fiob:.2f}", f"R$ {eco_m:.2f}", f"{pct:.1f}%",
            "Desconto ativo" if dv > 0 else "Encargo integral"
        ])

    cws2 = [40, 38, 54, 78, 78, 64, 82]
    tbl2 = Table(ftab, colWidths=cws2)
    tbl2.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0),  rlcolors.HexColor(AZ)),
        ("TEXTCOLOR",      (0,0), (-1,0),  rlcolors.white),
        ("FONTNAME",       (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,-1), 7.2),
        ("ALIGN",          (0,0), (-1,-1), "CENTER"),
        ("VALIGN",         (0,0), (-1,-1), "MIDDLE"),
        ("ROWHEIGHT",      (0,0), (-1,-1), 15.5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [rlcolors.HexColor(GR), rlcolors.white]),
        ("GRID",           (0,0), (-1,-1), 0.25, rlcolors.HexColor("#CCCCCC")),
        ("BACKGROUND",     (0,7), (-1,7),  rlcolors.HexColor("#FFEBEE")),
        ("FONTNAME",       (0,7), (-1,7),  "Helvetica-Bold"),
    ]))
    x2 = (W - sum(cws2)) / 2
    _, th2 = tbl2.wrapOn(c, sum(cws2), 400)
    tbl2.drawOn(c, x2, y-th2)
    y -= th2 + 8

    txt(c, "* Linha vermelha: encargo integral a partir do 6o ano",
        W/2, y, 7, "#999999", False, "center")
    y -= 18

    # Box conclusão
    rbox(c, M, y-50, W-2*M, 46, 8, "#E6F4EA", VD, 0.8)
    sf(c, VD); c.rect(M, y-50, 5, 46, fill=1, stroke=0)
    txt(c, "Mesmo com o Fio B, seu investimento e altamente rentavel!", M+12, y-16, 9.5, VD, True)
    txt(c, f"Economia total em 25 anos: {brl(dados['acum_25'])}   |   Lucro liquido: {brl(dados['roi'])}",
        M+12, y-30, 8.5, TX)
    txt(c, f"TIR mensal de {dados['tir']}% a.m. - superior a maioria das aplicacoes financeiras.",
        M+12, y-44, 8.5, TX)

    c.save(); buf.seek(0)
    return PdfReader(buf).pages[0]

# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÃO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════
def gerar_proposta(dados, output_path):
    # Campos derivados
    dados['geracao'] = math.ceil(dados['qtd_pai'] * 78.5)
    dados['parcela'] = round((dados['inv'] / 0.8471) / 18, 2)

    FIO_B = {1:1.0, 2:0.8, 3:0.6, 4:0.4, 5:0.2}
    av = 0; acum = []
    for i in range(1, 26):
        tar  = 0.92 * (1.05)**(i-1)
        gen  = dados['geracao'] * (0.995)**(i-1) * 12
        fiob = 0.26 * (1-FIO_B.get(i,0)) * (1.05)**(i-1)
        av  += gen*tar - gen*fiob
        acum.append(av)

    dados['acum_25'] = round(av, 2)
    dados['roi']     = round(av - dados['inv'], 2)
    dados['eco_mes'] = round(dados['geracao'] * 0.92, 2)
    dados['pb']      = round(dados['inv'] / dados['eco_mes'], 1) if dados['eco_mes'] > 0 else 0

    fluxo = [-dados['inv']] + [dados['eco_mes']] * 300
    r = 0.01
    for _ in range(500):
        pv  = sum(cv/(1+r)**t for t,cv in enumerate(fluxo))
        dpv = sum(-t*cv/(1+r)**(t+1) for t,cv in enumerate(fluxo))
        if abs(dpv) < 1e-10: break
        r  -= pv/dpv
    dados['tir'] = round(r*100, 2)

    template = PdfReader(TEMPLATE)
    writer   = PdfWriter()

    # Pag 1 — Capa
    pg0 = template.pages[0]; pg0.merge_page(overlay_capa(dados)); writer.add_page(pg0)
    # Pag 2, 3 — sem alteração
    writer.add_page(template.pages[1]); writer.add_page(template.pages[2])
    # Pag 4 — Equipamentos
    pg3 = template.pages[3]; pg3.merge_page(overlay_equipamentos(dados)); writer.add_page(pg3)
    # Pag 5 — Análise Financeira
    pg4 = template.pages[4]; pg4.merge_page(build_analise(dados, acum)); writer.add_page(pg4)
    # Pag 6 — Fio B
    pg5 = template.pages[5]; pg5.merge_page(build_fiob(dados, acum)); writer.add_page(pg5)
    # Pag 7 — Investimento
    pg6 = template.pages[6]; pg6.merge_page(overlay_investimento(dados)); writer.add_page(pg6)

    if hasattr(output_path, "write"):
        writer.write(output_path)
    else:
        with open(output_path, "wb") as f: writer.write(f)
    print(f"✅ Proposta gerada: {output_path}")
    print(f"   Geração: {dados['geracao']} kWh/mes")
    print(f"   Parcela 18x: {num(dados['parcela'])}")
    print(f"   Investimento: {num(dados['inv'])}")

# Teste
if __name__ == "__main__":
    dados = {
        "nome":      "Andre Mendes",
        "cidade":    "Salvador - BA",
        "kwh":       980,
        "qtd_pai":   12,
        "wp_pai":    620,
        "marca_pai": "Leapton",
        "qtd_inv":   3,
        "kw_inv":    2.25,
        "marca_inv": "Growatt",
        "tipo_inv":  "Microinversores",
        "inv":       17576.27,
        "tarifa":    0.92,
    }
    gerar_proposta(dados, "/home/claude/Proposta_v4.pdf")
