"""
Script de test pour la validation du contenu des fichiers uploadés
(magic bytes) sur /profile/photo et /profile/verification.

Vérifie que :
  1. Un faux fichier (texte renommé en .png) est bien REJETÉ (HTTP 400)
  2. Une vraie image PNG valide est bien ACCEPTÉE (HTTP 200)
  3. Même chose sur l'upload de document de vérification conducteur

Prérequis :
    pip install requests
    Le serveur backend doit tourner : uvicorn app.main:app --reload
    Un compte existant et déjà vérifié (email confirmé)

Lancement :
    python test_file_validation.py
"""

import base64
import requests

BASE_URL = "http://127.0.0.1:8000"

# PNG valide minimal (1x1 pixel transparent), encodé en base64.
# Suffisant pour que filetype.guess() le reconnaisse comme un vrai PNG.
_VALID_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
VALID_PNG_BYTES = base64.b64decode(_VALID_PNG_B64)

# Faux fichier : du texte brut, mais qu'on va envoyer avec un nom .png
# et un Content-Type "image/png" falsifié — exactement ce que l'ancien
# code (qui ne vérifiait que le Content-Type déclaré) aurait accepté.
FAKE_IMAGE_BYTES = b"Ceci n'est absolument pas une image, juste du texte brut."


def _title(text: str) -> None:
    print(f"\n{'=' * 70}\n{text}\n{'=' * 70}")


def _ok(text: str) -> None:
    print(f"  [OK]   {text}")


def _fail(text: str) -> None:
    print(f"  [FAIL] {text}")


def login(email: str, password: str) -> str | None:
    response = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if response.status_code != 200:
        _fail(f"Connexion échouée : {response.status_code} {response.text}")
        return None
    return response.json()["access_token"]


def test_profile_photo_upload(access_token: str) -> None:
    _title("Test — POST /profile/photo (validation magic bytes)")
    headers = {"Authorization": f"Bearer {access_token}"}

    # 1. Faux fichier avec Content-Type falsifié -> doit être rejeté
    fake_files = {"file": ("photo.png", FAKE_IMAGE_BYTES, "image/png")}
    fake_response = requests.post(f"{BASE_URL}/profile/photo", headers=headers, files=fake_files)
    if fake_response.status_code == 400:
        _ok(f"Faux fichier rejeté comme attendu (HTTP 400) : {fake_response.json().get('detail')}")
    else:
        _fail(
            f"Faux fichier NON rejeté (HTTP {fake_response.status_code}) — "
            "la validation par magic bytes ne semble pas active."
        )

    # 2. Vraie image PNG valide -> doit être acceptée
    real_files = {"file": ("photo.png", VALID_PNG_BYTES, "image/png")}
    real_response = requests.post(f"{BASE_URL}/profile/photo", headers=headers, files=real_files)
    if real_response.status_code == 200:
        _ok("Vraie image PNG acceptée (HTTP 200).")
    else:
        _fail(f"Vraie image PNG rejetée à tort : {real_response.status_code} {real_response.text}")


def test_driver_verification_upload(access_token: str) -> None:
    _title("Test — POST /profile/verification (validation magic bytes)")
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"document_type": "driving_license"}

    # 1. Faux fichier -> doit être rejeté
    fake_files = {"file": ("permis.png", FAKE_IMAGE_BYTES, "image/png")}
    fake_response = requests.post(
        f"{BASE_URL}/profile/verification", headers=headers, params=params, files=fake_files
    )
    if fake_response.status_code == 400:
        _ok(f"Faux document rejeté comme attendu (HTTP 400) : {fake_response.json().get('detail')}")
    else:
        _fail(
            f"Faux document NON rejeté (HTTP {fake_response.status_code}) — "
            "la validation par magic bytes ne semble pas active."
        )

    # 2. Vraie image -> doit être acceptée
    real_files = {"file": ("permis.png", VALID_PNG_BYTES, "image/png")}
    real_response = requests.post(
        f"{BASE_URL}/profile/verification", headers=headers, params=params, files=real_files
    )
    if real_response.status_code == 200:
        _ok("Vrai document (image PNG) accepté (HTTP 200).")
        _ok(f"Statut de vérification après upload : {real_response.json().get('driver_verification_status')}")
    else:
        _fail(f"Vrai document rejeté à tort : {real_response.status_code} {real_response.text}")


def main() -> None:
    print("Test de validation des uploads (magic bytes) — API TripMatch")
    print(f"Cible : {BASE_URL}")

    try:
        requests.get(BASE_URL, timeout=3)
    except requests.exceptions.ConnectionError:
        _fail(f"Impossible de joindre {BASE_URL}. Le serveur backend est-il lancé ?")
        return

    email = input("Email du compte de test (déjà vérifié) : ").strip()
    password = input("Mot de passe : ").strip()

    access_token = login(email, password)
    if not access_token:
        return

    test_profile_photo_upload(access_token)
    test_driver_verification_upload(access_token)

    _title("Terminé")
    print("Relisez les lignes [FAIL] ci-dessus si présentes — ce sont les points à corriger.")
    print("Note : ce test remplace votre vraie photo de profil et votre document de")
    print("vérification par les fichiers de test. Re-uploadez vos vrais fichiers après coup si besoin.")


if __name__ == "__main__":
    main()
