"""
Gestão Festa São Pedro 2026 — Sistema de Reserva de Mesas
App Streamlit: mapa de mesas, reservas, vendas, relatório. Dados no Google Sheets.
"""
import json
import os
import re
import time
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
import gspread
from gspread.exceptions import APIError as GspreadAPIError
from google.oauth2.service_account import Credentials
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Folha ofício (216 x 317 mm) — uma página
OFICIO = (216 * mm, 317 * mm)

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Gestão Festa São Pedro",
    page_icon="🎪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SHEET_ID = "1fvhCzt2ieZ4s-paXd3GLWgJho-9JE2oXCl14qKSpGDo"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
CACHE_TTL = 90  # segundos
IMAGEM_MAPA_PNG = "mapa.png"
IMAGEM_MAPA_JPG = "mapa.jpg"
IMAGEM_MAPA_JPG_ALT = "banda na praça (1).jpg"
ORDEM_SETORES = ["PATROCINADOR", "SETOR A", "SETOR B", "SETOR C"]
# Pasta onde está o app.py (para achar gcp_credenciais.txt e credentials.json)
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# -----------------------------------------------------------------------------
# CSS — layout e celular (9 mesas em uma fileira)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Fundo claro */
    .stApp { background: linear-gradient(180deg, #f5f7fa 0%, #e2e8f0 100%); }
    .main-header {
        background: linear-gradient(90deg, #edf2ff 0%, #c3dafe 50%, #edf2ff 100%);
        padding: 1rem 1.5rem; border-radius: 12px; margin-bottom: 1rem;
        box-shadow: 0 4px 20px rgba(15,23,42,0.2);
    }
    .main-header h1 { color: #1e293b; font-size: 1.75rem; margin: 0; }
    .main-header p { color: #334155; margin: 0.25rem 0 0 0; font-size: 0.9rem; }
    /* Métricas: número completo visível, sem cortar nem minimizar */
    [data-testid="stMetric"], [data-testid="stMetricValue"] {
        overflow: visible !important;
        white-space: nowrap !important;
        text-overflow: clip !important;
        min-width: fit-content !important;
    }
    [data-testid="stMetric"] p, [data-testid="stMetricValue"] p {
        overflow: visible !important;
        white-space: nowrap !important;
    }
    #MainMenu, footer, header { visibility: hidden; }
    @media (max-width: 768px) {
        [data-testid="stHorizontalBlock"]:has(> div:nth-child(9):nth-last-child(1)) {
            flex-wrap: nowrap !important; overflow-x: auto !important;
        }
        [data-testid="stHorizontalBlock"]:has(> div:nth-child(9):nth-last-child(1)) > div {
            flex: 0 0 11.11% !important; min-width: 0 !important; max-width: 11.11% !important;
        }
        .stButton > button { padding: 0.2rem 0.2rem !important; font-size: 0.65rem !important; min-height: 1.7rem !important; }
    }
    @media (max-width: 480px) {
        .stButton > button { padding: 0.15rem 0.12rem !important; font-size: 0.6rem !important; min-height: 1.55rem !important; }
    }
</style>
""", unsafe_allow_html=True)


def limpar_numero(valor):
    s = str(valor).upper().strip()
    if not s or s in ("NONE", "NAN"):
        return 0.0
    if "R$" in s or "," in s or "." in s:
        limpo = s.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
        try:
            return float(limpo)
        except ValueError:
            return 0.0
    nums = re.findall(r"\d+", s)
    return int(nums[0]) if nums else 0


def _normalizar_pem(info):
    """Corrige chave privada: \\n literal, private_key_base64, PEM em uma linha."""
    import copy
    info = copy.deepcopy(dict(info))
    key = (info.get("private_key") or "").strip()
    if not isinstance(key, str):
        return info
    # 1) private_key_base64: montar PEM a partir do base64
    b64_raw = info.get("private_key_base64")
    if b64_raw and isinstance(b64_raw, str):
        b64 = "".join(c for c in b64_raw if ord(c) < 128 and (c.isalnum() or c in "+/="))
        if len(b64) > 100:
            pem = "-----BEGIN PRIVATE KEY-----\n"
            for i in range(0, len(b64), 64):
                pem += b64[i : i + 64] + "\n"
            pem += "-----END PRIVATE KEY-----\n"
            info["private_key"] = pem
            info.pop("private_key_base64", None)
            return info
    # 2) Corrigir \n literal (string com \\n)
    if "\\n" in key:
        key = key.replace("\\n", "\n")
    # 3) Se a chave está em uma linha só (colou e perdeu quebras)
    if "-----BEGIN" in key and "-----END" in key and "\n" not in key:
        m = re.search(r"-----BEGIN[^-]+-----(.+?)-----END", key, re.DOTALL)
        if m:
            meio = "".join(c for c in m.group(1) if c.isalnum() or c in "+/=")
            if len(meio) > 100:
                pem = "-----BEGIN PRIVATE KEY-----\n"
                for i in range(0, len(meio), 64):
                    pem += meio[i : i + 64] + "\n"
                pem += "-----END PRIVATE KEY-----\n"
                key = pem
    # 4) Se ainda é uma linha longa só com base64 (sem BEGIN/END)
    if "\n" not in key and len(key) > 200:
        limpo = "".join(c for c in key if c.isalnum() or c in "+/=")
        if len(limpo) > 200:
            pem = "-----BEGIN PRIVATE KEY-----\n"
            for i in range(0, len(limpo), 64):
                pem += limpo[i : i + 64] + "\n"
            pem += "-----END PRIVATE KEY-----\n"
            key = pem
    # 5) Quebras de linha só \n (evitar \r no Windows)
    key = key.replace("\r\n", "\n").replace("\r", "\n")
    # 6) Manter só caracteres válidos do PEM (preservar \n)
    key = "".join(
        c for c in key
        if ord(c) < 128 and (c in "\n\r" or c.isalnum() or c in "+/=_- ")
    ).strip()
    info["private_key"] = key
    return info


@st.cache_resource
def conectar_gsheets():
    """Conexão com Google Sheets: env var → st.secrets (Streamlit Cloud) → gcp_credenciais.txt / credentials.json (local)."""
    env_json = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
    if env_json:
        try:
            info = json.loads(env_json)
            info = _normalizar_pem(info)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
            return gspread.authorize(creds).open_by_key(SHEET_ID)
        except Exception as e:
            err = str(e).lower()
            if "invalid_grant" in err or "jwt" in err or "signature" in err:
                st.error(
                    "**Erro de credenciais (Invalid JWT Signature)** — a chave privada está corrompida ou mal formatada.\n\n"
                    "**Local:** apague a variável **GCP_SERVICE_ACCOUNT_JSON** (se existir) ou rode `python gerar_json_credenciais.py` para gerar **gcp_credenciais.txt**."
                )
                st.stop()
            pass
    # Streamlit Cloud: st.secrets
    try:
        if "gcp_service_account" in st.secrets:
            info = _normalizar_pem(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
            return gspread.authorize(creds).open_by_key(SHEET_ID)
    except Exception:
        pass
    # Local: se existir gcp_credenciais.txt (JSON com private_key_base64), usa primeiro
    gcp_json_path = os.path.join(APP_DIR, "gcp_credenciais.txt")
    creds_path = os.path.join(APP_DIR, "credentials.json")
    if os.path.isfile(gcp_json_path):
        try:
            with open(gcp_json_path, encoding="utf-8-sig") as f:
                info = json.load(f)
            info = _normalizar_pem(info)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
            return gspread.authorize(creds).open_by_key(SHEET_ID)
        except Exception as e_gcp:
            pass  # cai no credentials.json
    # Local: credentials.json (direto; se falhar, tenta carregar + normalizar)
    try:
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        return gspread.authorize(creds).open_by_key(SHEET_ID)
    except Exception as e1:
        err1 = str(e1).lower()
        if "invalid_grant" in err1 or "jwt" in err1 or "signature" in err1 or "file" in err1 or "not found" in err1:
            try:
                with open(creds_path, encoding="utf-8-sig") as f:
                    info = json.load(f)
                info = _normalizar_pem(info)
                creds = Credentials.from_service_account_info(info, scopes=SCOPES)
                return gspread.authorize(creds).open_by_key(SHEET_ID)
            except Exception as e2:
                err2 = str(e2).lower()
                if "invalid_grant" in err2 or "jwt" in err2 or "signature" in err2:
                    st.error(
                        "**Erro de credenciais (Invalid JWT Signature)**\n\n"
                        "**1.** Rode no terminal: `python gerar_json_credenciais.py` (gera **gcp_credenciais.txt**). Depois rode de novo `streamlit run app.py` ou `python run_terminal.py`.\n\n"
                        "**2.** Se continuar: a chave pode estar **revogada**. No [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts) → sua conta → **Keys** → **Add Key** → **Create new key** → JSON. Substitua o **credentials.json** e rode de novo `python gerar_json_credenciais.py`."
                    )
                    st.stop()
                raise e2
        raise e1


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados():
    sh = conectar_gsheets()
    df = pd.DataFrame(sh.worksheet("Layout_Mesas").get_all_records())
    df["Linha_Num"] = df["Linha"].apply(limpar_numero)
    df["Coluna_Num"] = df["Coluna"].apply(limpar_numero)
    df["Preco_Num"] = df["Preco_Mesa"].apply(limpar_numero)
    df["Tipo_Item"] = df["Tipo_Item"].astype(str).str.strip().str.upper()
    df = df[df["Linha_Num"] > 0]
    try:
        df_res = pd.DataFrame(sh.worksheet("RESERVAS").get_all_records())
    except Exception:
        df_res = pd.DataFrame()
    return df, df_res


def salvar_reserva(dados):
    conectar_gsheets().worksheet("RESERVAS").append_row(dados)
    carregar_dados.clear()
    st.toast("Reserva salva com sucesso!", icon="✅")
    if "mesa_id" in st.session_state:
        st.session_state["mesa_id"] = None
    st.rerun()


def atualizar_status(id_venda, status, valor=0):
    sh = conectar_gsheets()
    ws = sh.worksheet("RESERVAS")
    cell = ws.find(id_venda)
    if cell:
        ws.update_cell(cell.row, 3, status)
        if status == "Vendido":
            ws.update_cell(cell.row, 7, valor)
            ws.update_cell(cell.row, 9, str(datetime.now()))
    carregar_dados.clear()
    st.toast("Status atualizado!", icon="💰")
    if "mesa_id" in st.session_state:
        st.session_state["mesa_id"] = None
    st.rerun()


def cancelar_reserva(id_venda):
    sh = conectar_gsheets()
    ws = sh.worksheet("RESERVAS")
    cell = ws.find(id_venda)
    if cell:
        ws.delete_rows(cell.row)
    carregar_dados.clear()
    st.toast("Reserva cancelada.", icon="🗑️")
    if "mesa_id" in st.session_state:
        st.session_state["mesa_id"] = None
    st.rerun()


def atualizar_valor_entrada(id_venda, valor_entrada):
    """Atualiza apenas o valor de entrada da reserva."""
    sh = conectar_gsheets()
    ws = sh.worksheet("RESERVAS")
    cell = ws.find(str(id_venda))
    if cell:
        ws.update_cell(cell.row, 7, valor_entrada)
    carregar_dados.clear()
    st.toast("Valor de entrada atualizado!", icon="💰")


def atualizar_celula_por_header(id_venda, header_name, value):
    """Atualiza uma célula da RESERVAS pelo nome da coluna (cabeçalho)."""
    for tentativa in range(3):
        try:
            sh = conectar_gsheets()
            ws = sh.worksheet("RESERVAS")
            headers = ws.row_values(1)
            if header_name not in headers:
                return
            cell = ws.find(str(id_venda))
            if cell:
                col = headers.index(header_name) + 1
                ws.update_cell(cell.row, col, str(value) if value is not None else "")
            return
        except GspreadAPIError:
            if tentativa == 2:
                raise
            time.sleep(1 + tentativa)


def gerar_pdf_extrato(ocupadas, total_mesas=None):
    """Gera PDF do extrato (vendas e reservas) em uma folha ofício. Retorna bytes."""
    buf = BytesIO()
    # Folha ofício 216x317 mm, margens menores para caber a tabela inteira
    largura_util = 216 * mm - 24  # margens 12+12
    doc = SimpleDocTemplate(buf, pagesize=OFICIO, rightMargin=12, leftMargin=12, topMargin=12, bottomMargin=12)
    cols = ["Numero_Display", "Status", "Nome_Cliente", "Telefone_Cliente", "Preco_Mesa", "Valor_Entrada_Cobrado", "Restante", "Metodo_Pagamento", "Parcelamento"]
    cols_base = [c for c in cols if c != "Restante" and c in ocupadas.columns]
    if "Restante" not in ocupadas.columns:
        cols_base.append("Restante")
    cols = cols_base if "Restante" in cols_base else cols_base + ["Restante"]
    headers = {"Numero_Display": "Mesa", "Status": "Status", "Nome_Cliente": "Cliente", "Telefone_Cliente": "Telefone", "Preco_Mesa": "Preço", "Valor_Entrada_Cobrado": "Valor cobrado", "Restante": "Restante", "Metodo_Pagamento": "Pagamento", "Parcelamento": "Parcelamento"}
    header_row = [headers.get(c, c) for c in cols]
    data = [header_row]
    for _, row in ocupadas.iterrows():
        linha = []
        for c in cols:
            if c == "Restante":
                preco = limpar_numero(row.get("Preco_Mesa", 0))
                entrada = limpar_numero(row.get("Valor_Entrada_Cobrado", 0))
                linha.append(str(max(0.0, preco - entrada)))
            else:
                linha.append(str(row.get(c, "")).replace("nan", ""))
        data.append(linha)
    # Larguras proporcionais à largura útil para caber numa folha ofício (inclui Restante)
    base_widths = [38, 52, 95, 78, 52, 58, 58, 62, 62][:len(cols)]
    total_base = sum(base_widths) or 1
    col_widths = [max(18, int(largura_util * w / total_base)) for w in base_widths]
    # Ajuste para soma = largura_util (evita overflow)
    soma = sum(col_widths)
    if soma > largura_util and soma > 0:
        col_widths = [max(18, int(w * largura_util / soma)) for w in col_widths]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("TOPPADDING", (0, 0), (-1, 0), 4),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("TOPPADDING", (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
    ]))
    styles = getSampleStyleSheet()
    titulo_style = styles["Title"]
    titulo_style.fontSize = 10
    titulo = Paragraph("Extrato — Gestão Festa São Pedro 2026", titulo_style)
    # Ocupação: mesas reservadas + vendidas sobre total
    ocup = len(ocupadas)
    total = total_mesas if total_mesas is not None and total_mesas > 0 else ocup
    pct = (100.0 * ocup / total) if total else 0
    texto_ocup = f"Ocupação (reservadas + vendidas): {ocup}/{total} mesas ({pct:.1f}%)"
    par_ocup = Paragraph(texto_ocup, styles["Normal"])
    doc.build([titulo, Spacer(1, 4), par_ocup, Spacer(1, 4), t])
    return buf.getvalue()


def desenhar_grade(setor_df, max_cols):
    for linha in sorted(setor_df["Linha_Num"].unique()):
        cols = st.columns(int(max_cols))
        for i, col in enumerate(cols):
            row_df = setor_df[(setor_df["Linha_Num"] == linha) & (setor_df["Coluna_Num"] == i + 1)]
            if row_df.empty:
                col.write("")
                continue
            d = row_df.iloc[0]
            st_mesa = d.get("Status")
            if st_mesa == "Vendido":
                lbl = f"🔴 {d['Numero_Display']}"
            elif st_mesa == "Reservado":
                lbl = f"🟡 {d['Numero_Display']}"
            else:
                lbl = f"🟢 {d['Numero_Display']}"
            if col.button(lbl, key=f"btn_{d['ID_Mesa']}", width="stretch"):
                st.session_state["mesa_id"] = d["ID_Mesa"]
                st.rerun()


# -----------------------------------------------------------------------------
# CARREGAR DADOS
# -----------------------------------------------------------------------------
try:
    df_layout, df_reservas = carregar_dados()
except Exception as e:
    err = str(e)
    if "429" in err or "Quota exceeded" in err or "RESOURCE_EXHAUSTED" in err:
        st.error("Limite do Google Sheets (60/min). Aguarde ~1 minuto e clique em **Atualizar dados**.")
        if st.button("🔄 Atualizar dados"):
            carregar_dados.clear()
            st.rerun()
    else:
        st.error(f"Erro de conexão: {e}")
    st.stop()

if not df_reservas.empty:
    df_res_limpo = df_reservas.sort_values("Data_Reserva", ascending=False).drop_duplicates(subset=["Ref_Mesa"])
    df_full = pd.merge(df_layout, df_res_limpo, left_on="ID_Mesa", right_on="Ref_Mesa", how="left")
else:
    df_full = df_layout.copy()
    df_full["Status"] = None

lookup_numero_para_id = {}
for _, row in df_full.iterrows():
    nd = str(row.get("Numero_Display", "")).strip()
    if not nd:
        continue
    id_mesa = row["ID_Mesa"]
    lookup_numero_para_id[nd.zfill(2)] = id_mesa
    lookup_numero_para_id[nd] = id_mesa

if "mesa_id" not in st.session_state:
    st.session_state["mesa_id"] = None
q = st.query_params.get("mesa")
if q is not None:
    try:
        num = int(q) if isinstance(q, str) else (int(q[0]) if q else 0)
        if 1 <= num <= 99:
            id_mesa = lookup_numero_para_id.get(f"{num:02d}") or lookup_numero_para_id.get(str(num))
            if id_mesa:
                st.session_state["mesa_id"] = id_mesa
    except (TypeError, ValueError):
        pass

total = len(df_full)
vendidas = df_full[df_full["Status"] == "Vendido"]
reservadas = df_full[df_full["Status"] == "Reservado"]
livres = total - len(vendidas) - len(reservadas)
caixa = vendidas["Valor_Entrada_Cobrado"].apply(limpar_numero).sum() if not vendidas.empty else 0
receber = reservadas["Preco_Num"].sum() if not reservadas.empty else 0
max_cols = int(df_full["Coluna_Num"].max()) if not df_full.empty else 9
perc_reservadas = (len(reservadas) / total * 100) if total > 0 else 0.0

# -----------------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🎪 Gestão Festa São Pedro 2026</h1>
    <p>Sistema de Reserva de Mesas</p>
</div>
""", unsafe_allow_html=True)

tab_mapa, tab_visual, tab_financeiro = st.tabs(["🗺️ Mapa de Mesas", "🖼️ Imagem do Mapa", "📊 Relatório"])

# --- Aba Mapa ---
with tab_mapa:
    m_id = st.session_state.get("mesa_id")

    # layout em duas colunas: mapa à esquerda, formulário à direita
    col_mapa, col_form = st.columns([2, 1])

    with col_mapa:
        st.subheader("Clique no botão da mesa")
        st.caption("🟢 Livre · 🟡 Reservado · 🔴 Vendido")
        for setor in ORDEM_SETORES:
            sub = df_full[df_full["Tipo_Item"] == setor]
            if not sub.empty:
                st.markdown(f"**{setor}**")
                desenhar_grade(sub, max_cols)
        for setor in df_full["Tipo_Item"].unique():
            if setor and setor not in ORDEM_SETORES:
                st.markdown(f"**{setor}**")
                desenhar_grade(df_full[df_full["Tipo_Item"] == setor], max_cols)

    with col_form:
        st.subheader("Detalhes da mesa")
        if not m_id:
            st.info("Clique em uma mesa no mapa para ver ou registrar a reserva aqui ao lado.")
        else:
            row = df_full[df_full["ID_Mesa"] == m_id]
            if not row.empty:
                d = row.iloc[0]
                status = d["Status"] if pd.notna(d["Status"]) else "Livre"
                st.markdown(f"### 📝 Mesa {d['Numero_Display']} — {status}")
                st.caption(f"Setor: {d.get('Tipo_Item', '-')} · Linha {d['Linha']}")
                if status == "Livre":
                    st.write(f"**Valor:** R$ {d['Preco_Mesa']}")
                    cli = st.text_input("Nome do cliente", key=f"cli_{m_id}")
                    tel = st.text_input("Telefone", key=f"tel_{m_id}")
                    fest = st.text_input("Festeiro (indicação)", key=f"fest_{m_id}")
                    b1, b2 = st.columns(2)
                    if b1.button("💾 Salvar reserva", type="primary", use_container_width=True):
                        if not (cli or "").strip():
                            st.error("Nome obrigatório.")
                        else:
                            salvar_reserva([
                                f"RES-{int(datetime.now().timestamp())}", m_id, "Reservado",
                                (cli or "").strip(), (fest or "").strip(), (tel or "").strip(),
                                "", str(datetime.now()), "", "", "",
                            ])
                    if b2.button("Fechar", use_container_width=True):
                        st.session_state["mesa_id"] = None
                        st.rerun()
                elif status == "Reservado":
                    st.warning(f"Reservado para **{d['Nome_Cliente']}** · 📞 {d.get('Telefone_Cliente', '-')}")
                    b1, b2, b3 = st.columns(3)
                    if b1.button("💲 Marcar pago", type="primary", use_container_width=True):
                        atualizar_status(d["ID_Venda"], "Vendido", d["Preco_Num"])
                    if b2.button("❌ Cancelar reserva", use_container_width=True):
                        cancelar_reserva(d["ID_Venda"])
                    if b3.button("Fechar", use_container_width=True):
                        st.session_state["mesa_id"] = None
                        st.rerun()
                elif status == "Vendido":
                    st.success(f"Vendido para **{d['Nome_Cliente']}**")
                    b1, b2 = st.columns(2)
                    if b1.button("Desfazer venda", use_container_width=True):
                        atualizar_status(d["ID_Venda"], "Reservado", 0)
                    if b2.button("Fechar", use_container_width=True):
                        st.session_state["mesa_id"] = None
                        st.rerun()

# --- Aba Imagem ---
with tab_visual:
    arquivo = None
    for nome in (IMAGEM_MAPA_PNG, IMAGEM_MAPA_JPG, IMAGEM_MAPA_JPG_ALT):
        if os.path.exists(nome):
            arquivo = nome
            break
    if arquivo:
        st.image(arquivo, caption="Layout do salão", width="stretch")
    else:
        st.warning(f"Coloque a imagem do mapa na pasta: **{IMAGEM_MAPA_PNG}** ou **{IMAGEM_MAPA_JPG}**.")

# --- Aba Relatório ---
with tab_financeiro:
    st.subheader("Resumo financeiro e ocupação")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("💰 Caixa", f"R$ {int(caixa)}")
    col2.metric("💸 A receber", f"R$ {int(receber)}")
    col3.metric("🔴 Vendidas", len(vendidas))
    col4.metric("🟡 Reservadas", len(reservadas))
    col5.metric("🟢 Livres", livres)
    col6.metric("🟡 % Reservadas", f"{perc_reservadas:.1f}%")
    st.divider()
    st.subheader("Extrato (vendas e reservas)")
    ocupadas = df_full[df_full["Status"].isin(["Vendido", "Reservado"])].copy()
    if not ocupadas.empty:
        base_cols = ["Numero_Display", "Status", "Nome_Cliente", "Telefone_Cliente", "Preco_Mesa", "Valor_Entrada_Cobrado", "Metodo_Pagamento", "Parcelamento"]
        for c in base_cols:
            if c not in ocupadas.columns:
                ocupadas[c] = ""
        cols = base_cols
        df_exibir = ocupadas[cols].copy()
        # coluna calculada: valor restante a receber (preço - entrada)
        df_exibir["Restante"] = df_exibir.apply(
            lambda r: max(
                limpar_numero(r.get("Preco_Mesa", 0)) - limpar_numero(r.get("Valor_Entrada_Cobrado", 0)),
                0,
            ),
            axis=1,
        )
        for c in df_exibir.columns:
            df_exibir[c] = df_exibir[c].astype(str).replace("nan", "")
        st.caption("Se **Metodo_Pagamento** e **Parcelamento** não existirem na planilha RESERVAS, adicione essas duas colunas na aba do Google Sheets para que apareçam e sejam salvas.")
        st.markdown("Edite **Status**, **Valor_Entrada_Cobrado**, **Metodo_Pagamento** e **Parcelamento**. As mudanças são salvas automaticamente.")
        edited = st.data_editor(
            df_exibir,
            width="stretch",
            hide_index=True,
            disabled=["Numero_Display", "Nome_Cliente", "Telefone_Cliente", "Preco_Mesa", "Restante"],
            key="editor_extrato",
        )

        # salvar automaticamente alterações em Status, Valor_Entrada_Cobrado, Metodo_Pagamento, Parcelamento
        houve_mudanca = False
        try:
            for idx in df_exibir.index:
                id_venda = ocupadas.loc[idx, "ID_Venda"]
                preco = float(limpar_numero(ocupadas.loc[idx, "Preco_Mesa"]))

                # Status
                status_antigo = str(df_exibir.at[idx, "Status"])
                status_novo = str(edited.at[idx, "Status"])
                if status_novo != status_antigo and status_novo in ("Reservado", "Vendido"):
                    if status_novo == "Vendido":
                        atualizar_status(id_venda, "Vendido", int(preco))
                    else:
                        atualizar_status(id_venda, "Reservado", 0)
                    houve_mudanca = True
                    continue

                # Valor de entrada
                entrada_antiga = float(limpar_numero(df_exibir.at[idx, "Valor_Entrada_Cobrado"]))
                entrada_nova = float(limpar_numero(edited.at[idx, "Valor_Entrada_Cobrado"]))
                if abs(entrada_nova - entrada_antiga) > 0.001:
                    atualizar_valor_entrada(id_venda, entrada_nova)
                    houve_mudanca = True

                # Metodo_Pagamento e Parcelamento
                for campo in ("Metodo_Pagamento", "Parcelamento"):
                    antigo = str(df_exibir.at[idx, campo])
                    novo = str(edited.at[idx, campo])
                    if novo != antigo:
                        atualizar_celula_por_header(id_venda, campo, novo)
                        houve_mudanca = True

            if houve_mudanca:
                carregar_dados.clear()
                st.rerun()
        except GspreadAPIError:
            st.error("Erro ao comunicar com o Google Sheets (limite de uso, permissões ou rede). Tente novamente em instantes.")

        pdf_bytes = gerar_pdf_extrato(ocupadas, total_mesas=len(df_full))
        st.download_button(
            "📄 Baixar extrato em PDF",
            data=pdf_bytes,
            file_name="extrato_mesas.pdf",
            mime="application/pdf",
            type="primary",
        )
    else:
        st.info("Nenhuma venda ou reserva ainda.")
