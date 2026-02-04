"""
Google Sheets — conexão e operações (mesmo backend do app Streamlit).
"""
import copy
import json
import os
import re
from datetime import datetime

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

SHEET_ID = "1fvhCzt2ieZ4s-paXd3GLWgJho-9JE2oXCl14qKSpGDo"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def limpar_numero(valor):
    s = str(valor).upper().strip()
    if not s or s in ("NONE", "NAN"):
        return 0.0
    if "R$" in s or "," in s or "." in s:
        limpo = s.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
        try:
            return float(limpo)
        except Exception:
            return 0.0
    nums = re.findall(r"\d+", s)
    return int(nums[0]) if nums else 0


def _normalizar_info_service_account(info):
    info = copy.deepcopy(dict(info))
    key = (info.get("private_key") or "").strip()
    if not isinstance(key, str):
        return info
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
    if "\\n" in key:
        key = key.replace("\\n", "\n")
    key = "".join(
        c for c in key
        if ord(c) < 128 and (c in "\n\r" or c.isalnum() or c in "+/=_- ")
    ).strip()
    info["private_key"] = key
    return info


def _conectar_gsheets():
    env_json = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
    if env_json:
        try:
            info = json.loads(env_json)
            info = _normalizar_info_service_account(info)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
            return gspread.authorize(creds).open_by_key(SHEET_ID)
        except Exception:
            pass
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    return gspread.authorize(creds).open_by_key(SHEET_ID)


def carregar_dados():
    sh = _conectar_gsheets()
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


def obter_df_full():
    df_layout, df_reservas = carregar_dados()
    if not df_reservas.empty:
        df_res_limpo = (
            df_reservas.sort_values("Data_Reserva", ascending=False)
            .drop_duplicates(subset=["Ref_Mesa"])
        )
        df_full = pd.merge(
            df_layout, df_res_limpo, left_on="ID_Mesa", right_on="Ref_Mesa", how="left"
        )
    else:
        df_full = df_layout.copy()
        df_full["Status"] = None
    return df_full


def lookup_numero_para_id(df_full):
    lookup = {}
    for _, row in df_full.iterrows():
        nd = str(row.get("Numero_Display", "")).strip()
        if not nd:
            continue
        id_mesa = row["ID_Mesa"]
        lookup[nd.zfill(2)] = id_mesa
        lookup[nd] = id_mesa
    return lookup


def salvar_reserva(id_mesa, nome_cliente, festeiro, telefone):
    sh = _conectar_gsheets()
    dados = [
        f"RES-{int(datetime.now().timestamp())}",
        id_mesa,
        "Reservado",
        nome_cliente,
        festeiro or "",
        telefone or "",
        "",
        str(datetime.now()),
        "",
    ]
    sh.worksheet("RESERVAS").append_row(dados)


def atualizar_status(id_venda, status, valor=0):
    sh = _conectar_gsheets()
    ws = sh.worksheet("RESERVAS")
    cell = ws.find(id_venda)
    if cell:
        ws.update_cell(cell.row, 3, status)
        if status == "Vendido":
            ws.update_cell(cell.row, 7, valor)
            ws.update_cell(cell.row, 9, str(datetime.now()))


def cancelar_reserva(id_venda):
    sh = _conectar_gsheets()
    ws = sh.worksheet("RESERVAS")
    cell = ws.find(id_venda)
    if cell:
        ws.delete_rows(cell.row)
