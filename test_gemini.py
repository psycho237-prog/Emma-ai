"""Test avec gemini-flash-latest (timeout augmente)"""
import requests

key = "AIzaSyCR3fwooydM-462KubGRGZj9DgCl0S5Gt4"
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={key}"

payload = {
    "contents": [{"parts": [{"text": "Ceci est un test pour l'assistante EMMA. Reponds 'OK'."}]}]
}

print("Test final avec gemini-flash-latest...")
try:
    r = requests.post(url, json=payload, timeout=20)
    if r.status_code == 200:
        data = r.json()
        print(f"Gemini dit: {data['candidates'][0]['content']['parts'][0]['text']}")
        print("\n>>> OK ! CLE ET MODELE VALIDES. <<<")
    else:
        print(f"Erreur {r.status_code}: {r.json()}")
except Exception as e:
    print(f"Echec: {e}")
