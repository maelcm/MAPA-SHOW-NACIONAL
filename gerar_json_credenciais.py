"""
Gera gcp_credenciais.txt a partir do credentials.json (JSON com private_key_base64).
Use para o terminal: o run_terminal.py e o app Streamlit usam esse arquivo se existir.
"""
import json
import re

with open("credentials.json", encoding="utf-8") as f:
    data = json.load(f)

key = (data.get("private_key") or "").strip()
key = key.replace("\\n", "\n")
m = re.search(r"-----BEGIN[^-]+-----(.+?)-----END", key, re.DOTALL)
if m:
    b64 = "".join(c for c in m.group(1) if c.isalnum() or c in "+/=")
else:
    b64 = "".join(c for c in key if c.isalnum() or c in "+/=")

out = {k: v for k, v in data.items() if k != "private_key"}
out["private_key_base64"] = b64

json_credenciais = json.dumps(out, ensure_ascii=False, separators=(",", ":"))

with open("gcp_credenciais.txt", "w", encoding="utf-8") as f:
    f.write(json_credenciais)

print("Arquivo gcp_credenciais.txt criado. O terminal e o app usam esse arquivo automaticamente.")
print("\nConteúdo (uma linha):")
print(json_credenciais[:80] + "...")
