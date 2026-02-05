"""
Testa se as credenciais (gcp_credenciais.txt ou credentials.json) funcionam.
Rode: python testar_credenciais.py
"""
import json
import os
import re

SHEET_ID = "1fvhCzt2ieZ4s-paXd3GLWgJho-9JE2oXCl14qKSpGDo"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def _normalizar_pem(info):
    info = dict(info)
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
    key = key.replace("\r\n", "\n").replace("\r", "\n")
    key = "".join(c for c in key if ord(c) < 128 and (c in "\n\r" or c.isalnum() or c in "+/=_- ")).strip()
    info["private_key"] = key
    return info

def main():
    from google.oauth2.service_account import Credentials
    import gspread

    base = os.path.dirname(os.path.abspath(__file__))
    gcp_txt = os.path.join(base, "gcp_credenciais.txt")
    creds_json = os.path.join(base, "credentials.json")

    for nome, path in [("gcp_credenciais.txt", gcp_txt), ("credentials.json", creds_json)]:
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8-sig") as f:
                info = json.load(f)
            info = _normalizar_pem(info)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
            gc = gspread.authorize(creds)
            sh = gc.open_by_key(SHEET_ID)
            sh.worksheet("Layout_Mesas").get_all_records()
            print(f"OK — credenciais funcionam (usando {nome})")
            return
        except Exception as e:
            print(f"Erro com {nome}: {e}")
    print("Nenhum arquivo de credenciais funcionou. Crie uma nova chave no Google Cloud e rode python gerar_json_credenciais.py")

if __name__ == "__main__":
    main()
