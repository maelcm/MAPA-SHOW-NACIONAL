"""
Views — Mapa de Mesas, formulário de reserva, relatório, imagem do mapa.
"""
import os
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

from . import services

ORDEM_SETORES = ["PATROCINADOR", "SETOR A", "SETOR B", "SETOR C"]
IMAGEM_MAPA_PNG = "mapa.png"
IMAGEM_MAPA_JPG = "mapa.jpg"
IMAGEM_MAPA_JPG_ALT = "banda na praça (1).jpg"


def _build_setores(df_full, max_cols):
    """Monta estrutura setor -> listas de linhas -> listas de mesas por coluna."""
    from collections import OrderedDict
    setores = OrderedDict()
    for setor in ORDEM_SETORES:
        sub = df_full[df_full["Tipo_Item"] == setor]
        if sub.empty:
            continue
        rows = []
        for linha in sorted(sub["Linha_Num"].unique()):
            row_mesas = []
            for col in range(1, int(max_cols) + 1):
                m = sub[(sub["Linha_Num"] == linha) & (sub["Coluna_Num"] == col)]
                row_mesas.append(m.iloc[0].to_dict() if not m.empty else None)
            rows.append(row_mesas)
        setores[setor] = rows
    outros = [s for s in df_full["Tipo_Item"].unique() if s and s not in ORDEM_SETORES]
    for setor in outros:
            sub = df_full[df_full["Tipo_Item"] == setor]
            if sub.empty:
                continue
            rows = []
            for linha in sorted(sub["Linha_Num"].unique()):
                row_mesas = []
                for col in range(1, int(max_cols) + 1):
                    m = sub[(sub["Linha_Num"] == linha) & (sub["Coluna_Num"] == col)]
                    row_mesas.append(m.iloc[0].to_dict() if not m.empty else None)
                rows.append(row_mesas)
            setores[setor] = rows
    return setores


def _get_context_base():
    try:
        df_full = services.obter_df_full()
    except Exception as e:
        err = str(e)
        if "429" in err or "Quota exceeded" in err or "RESOURCE_EXHAUSTED" in err:
            return None, {"erro": "Limite do Google Sheets (60/min). Aguarde ~1 minuto."}
        return None, {"erro": f"Erro de conexão: {e}"}

    lookup = services.lookup_numero_para_id(df_full)
    total = len(df_full)
    vendidas = df_full[df_full["Status"] == "Vendido"]
    reservadas = df_full[df_full["Status"] == "Reservado"]
    livres = total - len(vendidas) - len(reservadas)
    caixa = vendidas["Valor_Entrada_Cobrado"].apply(services.limpar_numero).sum() if not vendidas.empty else 0
    receber = reservadas["Preco_Num"].sum() if not reservadas.empty else 0
    max_cols = int(df_full["Coluna_Num"].max()) if not df_full.empty else 9
    setores = _build_setores(df_full, max_cols)

    return df_full, {
        "setores": setores,
        "max_cols": max_cols,
        "lookup_numero_para_id": lookup,
        "total": total,
        "livres": livres,
        "vendidas_count": len(vendidas),
        "reservadas_count": len(reservadas),
        "caixa": caixa,
        "receber": receber,
        "ordem_setores": ORDEM_SETORES,
        "erro": None,
    }


def home(request):
    df_full, ctx = _get_context_base()
    if df_full is None:
        return render(request, "mesas/erro.html", ctx)

    mesa_id = request.GET.get("mesa")
    if mesa_id:
        try:
            num = int(mesa_id)
            if 1 <= num <= 99:
                lookup = ctx["lookup_numero_para_id"]
                id_mesa = lookup.get(f"{num:02d}") or lookup.get(str(num))
                if id_mesa:
                    return redirect("mesa_detail", id_mesa=id_mesa)
        except (TypeError, ValueError):
            pass

    ctx["mesa_selecionada_id"] = None
    return render(request, "mesas/index.html", ctx)


def mesa_detail(request, id_mesa):
    df_full, ctx = _get_context_base()
    if df_full is None:
        return render(request, "mesas/erro.html", ctx)

    row = df_full[df_full["ID_Mesa"] == id_mesa]
    if row.empty:
        return redirect("home")

    mesa = row.iloc[0]
    # converter Series para dict (valores podem ser numpy types)
    mesa_dict = {k: (v.item() if hasattr(v, "item") else v) for k, v in mesa.items()}
    status = mesa_dict.get("Status") if mesa_dict.get("Status") else "Livre"
    ctx["mesa"] = mesa_dict
    ctx["mesa_status"] = status
    ctx["mesa_selecionada_id"] = id_mesa
    return render(request, "mesas/index.html", ctx)


@require_http_methods(["POST"])
def mesa_reservar(request, id_mesa):
    nome = (request.POST.get("nome_cliente") or "").strip()
    if not nome:
        return redirect("mesa_detail", id_mesa=id_mesa)
    festeiro = (request.POST.get("festeiro") or "").strip()
    telefone = (request.POST.get("telefone") or "").strip()
    services.salvar_reserva(id_mesa, nome, festeiro, telefone)
    return redirect("mesa_detail", id_mesa=id_mesa)


@require_http_methods(["POST"])
def mesa_marcar_pago(request, id_mesa):
    id_venda = request.POST.get("id_venda")
    if id_venda:
        try:
            df_full = services.obter_df_full()
            row = df_full[df_full["ID_Mesa"] == id_mesa]
            if not row.empty:
                preco = row.iloc[0].get("Preco_Num", 0)
                services.atualizar_status(id_venda, "Vendido", preco)
        except Exception:
            pass
    return redirect("mesa_detail", id_mesa=id_mesa)


@require_http_methods(["POST"])
def mesa_cancelar_reserva(request, id_mesa):
    id_venda = request.POST.get("id_venda")
    if id_venda:
        services.cancelar_reserva(id_venda)
    return redirect("mesa_detail", id_mesa=id_mesa)


@require_http_methods(["POST"])
def mesa_desfazer_venda(request, id_mesa):
    id_venda = request.POST.get("id_venda")
    if id_venda:
        services.atualizar_status(id_venda, "Reservado", 0)
    return redirect("mesa_detail", id_mesa=id_mesa)


def relatorio(request):
    df_full, ctx = _get_context_base()
    if df_full is None:
        return render(request, "mesas/erro.html", ctx)
    ocupadas = df_full[df_full["Status"].isin(["Vendido", "Reservado"])]
    ctx["ocupadas"] = ocupadas.to_dict("records") if not ocupadas.empty else []
    return render(request, "mesas/relatorio.html", ctx)


def imagem_mapa(request):
    for nome in (IMAGEM_MAPA_PNG, IMAGEM_MAPA_JPG, IMAGEM_MAPA_JPG_ALT):
        if os.path.exists(nome):
            with open(nome, "rb") as f:
                content = f.read()
            content_type = "image/png" if nome.endswith(".png") else "image/jpeg"
            return HttpResponse(content, content_type=content_type)
    return HttpResponse("Imagem do mapa não encontrada.", status=404)
