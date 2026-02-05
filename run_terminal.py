"""
Gestão Festa São Pedro 2026 — Versão terminal (sem Streamlit).
Rode: python run_terminal.py
"""
import copy
import json
import os
import re
import sys
from datetime import datetime

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1fvhCzt2ieZ4s-paXd3GLWgJho-9JE2oXCl14qKSpGDo"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
ORDEM_SETORES = ["PATROCINADOR", "SETOR A", "SETOR B", "SETOR C"]
APP_DIR = os.path.dirname(os.path.abspath(__file__))


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
    if "\n" not in key and len(key) > 200:
        limpo = "".join(c for c in key if c.isalnum() or c in "+/=")
        if len(limpo) > 200:
            pem = "-----BEGIN PRIVATE KEY-----\n"
            for i in range(0, len(limpo), 64):
                pem += limpo[i : i + 64] + "\n"
            pem += "-----END PRIVATE KEY-----\n"
            key = pem
    key = key.replace("\r\n", "\n").replace("\r", "\n")
    key = "".join(c for c in key if ord(c) < 128 and (c in "\n\r" or c.isalnum() or c in "+/=_- ")).strip()
    info["private_key"] = key
    return info


def conectar_gsheets():
    gcp_json_path = os.path.join(APP_DIR, "gcp_credenciais.txt")
    creds_path = os.path.join(APP_DIR, "credentials.json")
    env_json = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
    if env_json:
        try:
            info = json.loads(env_json)
            info = _normalizar_pem(info)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
            return gspread.authorize(creds).open_by_key(SHEET_ID)
        except Exception:
            pass
    if os.path.isfile(gcp_json_path):
        try:
            with open(gcp_json_path, encoding="utf-8-sig") as f:
                info = json.load(f)
            info = _normalizar_pem(info)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
            return gspread.authorize(creds).open_by_key(SHEET_ID)
        except Exception:
            pass
    try:
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        return gspread.authorize(creds).open_by_key(SHEET_ID)
    except Exception:
        pass
    try:
        with open(creds_path, encoding="utf-8-sig") as f:
            info = json.load(f)
        info = _normalizar_pem(info)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        return gspread.authorize(creds).open_by_key(SHEET_ID)
    except Exception as e:
        print(f"Erro de credenciais: {e}")
        if "invalid_grant" in str(e).lower() or "jwt" in str(e).lower():
            print("\nA chave pode estar revogada. Crie uma nova chave no Google Cloud:")
            print("  https://console.cloud.google.com/iam-admin/serviceaccounts")
            print("  → sua conta → Keys → Add Key → Create new key → JSON")
            print("Substitua o credentials.json na pasta e rode: python gerar_json_credenciais.py")
        else:
            print("Coloque credentials.json na pasta ou rode: python gerar_json_credenciais.py")
        sys.exit(1)


def carregar_dados(sh):
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


def mesclar_layout_reservas(df_layout, df_reservas):
    if not df_reservas.empty:
        df_limpo = df_reservas.sort_values("Data_Reserva", ascending=False).drop_duplicates(subset=["Ref_Mesa"])
        df_full = pd.merge(df_layout, df_limpo, left_on="ID_Mesa", right_on="Ref_Mesa", how="left")
    else:
        df_full = df_layout.copy()
        df_full["Status"] = None
    return df_full


def main():
    print("Conectando ao Google Sheets...")
    sh = conectar_gsheets()
    print("Conectado.\n")

    while True:
        df_layout, df_reservas = carregar_dados(sh)
        df_full = mesclar_layout_reservas(df_layout, df_reservas)
        vendidas = df_full[df_full["Status"] == "Vendido"]
        reservadas = df_full[df_full["Status"] == "Reservado"]
        livres = len(df_full) - len(vendidas) - len(reservadas)
        caixa = vendidas["Valor_Entrada_Cobrado"].apply(limpar_numero).sum() if not vendidas.empty else 0
        receber = reservadas["Preco_Num"].sum() if not reservadas.empty else 0

        print("=" * 50)
        print("  GESTÃO FESTA SÃO PEDRO 2026 — Terminal")
        print("=" * 50)
        print(f"  Caixa: R$ {int(caixa)}  |  A receber: R$ {int(receber)}")
        print(f"  Vendidas: {len(vendidas)}  |  Reservadas: {len(reservadas)}  |  Livres: {livres}")
        print("=" * 50)
        print("  1 - Ver mapa de mesas (por setor)")
        print("  2 - Ver extrato (vendas e reservas)")
        print("  3 - Fazer reserva")
        print("  4 - Marcar mesa como vendida")
        print("  5 - Cancelar reserva")
        print("  6 - Atualizar dados")
        print("  0 - Sair")
        print("-" * 50)
        op = input("Opção: ").strip()

        if op == "0":
            print("Até logo.")
            break
        if op == "1":
            for setor in ORDEM_SETORES:
                sub = df_full[df_full["Tipo_Item"] == setor]
                if sub.empty:
                    continue
                print(f"\n--- {setor} ---")
                for _, row in sub.sort_values(["Linha_Num", "Coluna_Num"]).iterrows():
                    st = row.get("Status") or "Livre"
                    if st == "Vendido":
                        s = "🔴"
                    elif st == "Reservado":
                        s = "🟡"
                    else:
                        s = "🟢"
                    print(f"  {s} Mesa {row['Numero_Display']} ({row.get('Preco_Mesa', '-')})")
            for setor in df_full["Tipo_Item"].unique():
                if setor and setor not in ORDEM_SETORES:
                    sub = df_full[df_full["Tipo_Item"] == setor]
                    if sub.empty:
                        continue
                    print(f"\n--- {setor} ---")
                    for _, row in sub.sort_values(["Linha_Num", "Coluna_Num"]).iterrows():
                        st = row.get("Status") or "Livre"
                        s = "🔴" if st == "Vendido" else ("🟡" if st == "Reservado" else "🟢")
                        print(f"  {s} Mesa {row['Numero_Display']}")
            input("\n[Enter] para continuar...")
            continue
        if op == "2":
            ocupadas = df_full[df_full["Status"].isin(["Vendido", "Reservado"])]
            if ocupadas.empty:
                print("Nenhuma venda ou reserva.")
            else:
                cols = ["Numero_Display", "Status", "Nome_Cliente", "Telefone_Cliente", "Preco_Mesa", "Valor_Entrada_Cobrado"]
                print(pd.DataFrame(ocupadas[cols]).to_string(index=False))
            input("\n[Enter] para continuar...")
            continue
        if op == "3":
            num = input("Número da mesa (ex: 5): ").strip()
            nome = input("Nome do cliente: ").strip()
            if not nome:
                print("Nome obrigatório.")
                input("[Enter]...")
                continue
            tel = input("Telefone: ").strip()
            fest = input("Festeiro (indicação): ").strip()
            row = df_full[df_full["Numero_Display"].astype(str).str.strip() == num]
            if row.empty:
                row = df_full[df_full["Numero_Display"].astype(str).str.zfill(2) == num.zfill(2)]
            if row.empty:
                print("Mesa não encontrada.")
                input("[Enter]...")
                continue
            d = row.iloc[0]
            if pd.notna(d.get("Status")) and str(d.get("Status")) not in ("", "Livre", "nan"):
                print("Mesa já ocupada ou reservada.")
                input("[Enter]...")
                continue
            id_mesa = d["ID_Mesa"]
            id_venda = f"RES-{int(datetime.now().timestamp())}"
            sh.worksheet("RESERVAS").append_row([
                id_venda, id_mesa, "Reservado", nome, fest, tel, "", str(datetime.now()), "", ""
            ])
            print("Reserva salva com sucesso.")
            input("[Enter]...")
            continue
        if op == "4":
            num = input("Número da mesa a marcar como vendida: ").strip()
            row = df_full[(df_full["Numero_Display"].astype(str).str.strip() == num) | (df_full["Numero_Display"].astype(str).str.zfill(2) == num.zfill(2))]
            if row.empty:
                print("Mesa não encontrada.")
                input("[Enter]...")
                continue
            d = row.iloc[0]
            id_venda = d.get("ID_Venda")
            if pd.isna(id_venda) or not id_venda:
                print("Mesa livre — faça primeiro uma reserva (opção 3).")
                input("[Enter]...")
                continue
            ws = sh.worksheet("RESERVAS")
            cell = ws.find(str(id_venda))
            if cell:
                ws.update_cell(cell.row, 3, "Vendido")
                ws.update_cell(cell.row, 7, str(d.get("Preco_Num", 0)))
                ws.update_cell(cell.row, 9, str(datetime.now()))
            print("Marcado como vendido.")
            input("[Enter]...")
            continue
        if op == "5":
            num = input("Número da mesa para cancelar reserva: ").strip()
            row = df_full[(df_full["Numero_Display"].astype(str).str.strip() == num) | (df_full["Numero_Display"].astype(str).str.zfill(2) == num.zfill(2))]
            if row.empty:
                print("Mesa não encontrada.")
                input("[Enter]...")
                continue
            d = row.iloc[0]
            id_venda = d.get("ID_Venda")
            if pd.isna(id_venda) or not id_venda:
                print("Mesa não está reservada.")
                input("[Enter]...")
                continue
            ws = sh.worksheet("RESERVAS")
            cell = ws.find(str(id_venda))
            if cell:
                ws.delete_rows(cell.row)
            print("Reserva cancelada.")
            input("[Enter]...")
            continue
        if op == "6":
            print("Dados atualizados.")
            continue
        print("Opção inválida.")


if __name__ == "__main__":
    main()
