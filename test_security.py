"""
Script de test de sécurité pour l'API TripMatch.

Vérifie concrètement :
  1. Le rate limiting sur /auth/login (doit se déclencher après 10 tentatives/minute)
  2. Le rate limiting sur /auth/register (5/heure)
  3. Le rate limiting sur /auth/forgot-password (3/heure) + réponse anti-énumération
  4. Le flux /auth/refresh (refresh_token valide -> nouveau access_token)
  5. Qu'un token invalide/absent est bien rejeté sur une route protégée

Prérequis :
    pip install requests
    Le serveur backend doit tourner : uvicorn app.main:app --reload

Lancement :
    python test_security.py

Le script est volontairement autonome (pas de dépendance à pytest) pour
pouvoir être relancé rapidement pendant les tests manuels.
"""

import time
import uuid

import requests

BASE_URL = "http://127.0.0.1:8000"


# ---------------------------------------------------------------------------
# Utilitaires d'affichage
# ---------------------------------------------------------------------------

def _title(text: str) -> None:
    print(f"\n{'=' * 70}\n{text}\n{'=' * 70}")


def _ok(text: str) -> None:
    print(f"  [OK]   {text}")


def _fail(text: str) -> None:
    print(f"  [FAIL] {text}")


def _info(text: str) -> None:
    print(f"  [INFO] {text}")


# ---------------------------------------------------------------------------
# Test 1 — Rate limiting sur /auth/login
# ---------------------------------------------------------------------------

def test_login_rate_limit() -> None:
    _title("Test 1 — Rate limiting sur /auth/login (limite attendue : 10/minute)")

    payload = {"email": "nonexistent_user_rate_test@example.com", "password": "wrong-password"}

    statuses = []
    for i in range(1, 13):
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        statuses.append(response.status_code)
        print(f"  Tentative {i:2d}: HTTP {response.status_code}")

    if 429 in statuses:
        first_429_index = statuses.index(429) + 1
        _ok(f"Rate limit déclenché à la tentative {first_429_index} (HTTP 429 reçu).")
    else:
        _fail("Aucun HTTP 429 reçu après 12 tentatives. Le rate limiting ne semble pas actif sur /auth/login.")


# ---------------------------------------------------------------------------
# Test 2 — Rate limiting sur /auth/register
# ---------------------------------------------------------------------------

def test_register_rate_limit() -> None:
    _title("Test 2 — Rate limiting sur /auth/register (limite attendue : 5/heure)")

    statuses = []
    for i in range(1, 8):
        unique_email = f"rate_test_{uuid.uuid4().hex[:10]}@example.com"
        payload = {"email": unique_email, "password": "TestPassword123"}
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        statuses.append(response.status_code)
        print(f"  Tentative {i}: HTTP {response.status_code} (email: {unique_email})")

    if 429 in statuses:
        first_429_index = statuses.index(429) + 1
        _ok(f"Rate limit déclenché à la tentative {first_429_index} (HTTP 429 reçu).")
    else:
        _fail("Aucun HTTP 429 reçu après 7 tentatives. Le rate limiting ne semble pas actif sur /auth/register.")
        _info("Note : chaque tentative réussie crée un vrai compte en base — pensez à nettoyer si besoin.")


# ---------------------------------------------------------------------------
# Test 3 — Rate limiting + anti-énumération sur /auth/forgot-password
# ---------------------------------------------------------------------------

def test_forgot_password_rate_limit_and_enumeration() -> None:
    _title("Test 3 — /auth/forgot-password (rate limit 3/heure + anti-énumération)")

    # 3a. Anti-énumération : email existant vs inexistant doivent donner la même réponse
    existing_email_payload = {"email": "some_existing_or_not_email@example.com"}
    nonexistent_email_payload = {"email": f"definitely_not_registered_{uuid.uuid4().hex[:8]}@example.com"}

    resp_a = requests.post(f"{BASE_URL}/auth/forgot-password", json=existing_email_payload)
    resp_b = requests.post(f"{BASE_URL}/auth/forgot-password", json=nonexistent_email_payload)

    if resp_a.status_code == resp_b.status_code == 200 and resp_a.json() == resp_b.json():
        _ok("Réponse identique pour email existant et inexistant (anti-énumération respectée).")
    else:
        _fail(
            f"Réponses différentes détectées — fuite d'information possible. "
            f"Réponse A: {resp_a.status_code} {resp_a.text} | Réponse B: {resp_b.status_code} {resp_b.text}"
        )

    # 3b. Rate limiting (3/heure)
    statuses = []
    for i in range(1, 6):
        payload = {"email": f"rate_test_forgot_{uuid.uuid4().hex[:8]}@example.com"}
        response = requests.post(f"{BASE_URL}/auth/forgot-password", json=payload)
        statuses.append(response.status_code)
        print(f"  Tentative {i}: HTTP {response.status_code}")

    if 429 in statuses:
        first_429_index = statuses.index(429) + 1
        _ok(f"Rate limit déclenché à la tentative {first_429_index} (HTTP 429 reçu).")
    else:
        _fail("Aucun HTTP 429 reçu. Le rate limiting ne semble pas actif sur /auth/forgot-password.")


# ---------------------------------------------------------------------------
# Test 4 — Flux /auth/refresh
# ---------------------------------------------------------------------------

def test_refresh_flow(email: str, password: str) -> None:
    _title("Test 4 — Flux /auth/refresh")

    login_resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if login_resp.status_code != 200:
        _fail(
            f"Impossible de se connecter avec le compte fourni ({login_resp.status_code}: {login_resp.text}). "
            "Test /auth/refresh ignoré — fournissez un email/mot de passe valides et vérifiés."
        )
        return

    tokens = login_resp.json()
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        _fail("La réponse de /auth/login ne contient pas de refresh_token.")
        return
    _ok("Connexion réussie, refresh_token récupéré.")

    refresh_resp = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": refresh_token})
    if refresh_resp.status_code == 200:
        new_tokens = refresh_resp.json()
        if new_tokens.get("access_token") and new_tokens.get("refresh_token"):
            _ok("POST /auth/refresh a renvoyé un nouveau access_token et un nouveau refresh_token.")
        else:
            _fail(f"Réponse /auth/refresh incomplète : {new_tokens}")
    else:
        _fail(f"POST /auth/refresh a échoué : {refresh_resp.status_code} {refresh_resp.text}")
        return

    # Vérifie qu'un refresh_token invalide est bien rejeté
    bad_refresh_resp = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": "token.invalide.bidon"})
    if bad_refresh_resp.status_code == 401:
        _ok("Un refresh_token invalide est correctement rejeté (HTTP 401).")
    else:
        _fail(f"Un refresh_token invalide n'a pas été rejeté comme attendu : {bad_refresh_resp.status_code}")

    # Vérifie qu'un access_token ne peut pas être utilisé comme refresh_token
    access_token = tokens.get("access_token")
    if access_token:
        wrong_type_resp = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": access_token})
        if wrong_type_resp.status_code == 401:
            _ok("Un access_token utilisé comme refresh_token est correctement rejeté (HTTP 401).")
        else:
            _fail(
                f"Un access_token utilisé comme refresh_token n'a pas été rejeté : {wrong_type_resp.status_code}"
            )


# ---------------------------------------------------------------------------
# Test 5 — Protection des routes authentifiées
# ---------------------------------------------------------------------------

def test_protected_route_without_token() -> None:
    _title("Test 5 — Accès à une route protégée sans token")

    response = requests.get(f"{BASE_URL}/auth/me")
    if response.status_code in (401, 403):
        _ok(f"GET /auth/me sans token renvoie bien {response.status_code} (accès refusé).")
    else:
        _fail(f"GET /auth/me sans token a renvoyé {response.status_code} au lieu de 401/403 — faille potentielle.")

    bad_token_response = requests.get(
        f"{BASE_URL}/auth/me", headers={"Authorization": "Bearer token.completement.invalide"}
    )
    if bad_token_response.status_code == 401:
        _ok("GET /auth/me avec un token invalide renvoie bien 401.")
    else:
        _fail(f"GET /auth/me avec un token invalide a renvoyé {bad_token_response.status_code} au lieu de 401.")


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main() -> None:
    print("Tests de sécurité — API TripMatch")
    print(f"Cible : {BASE_URL}")
    print("Assurez-vous que le serveur tourne (uvicorn app.main:app --reload) avant de continuer.")

    try:
        requests.get(BASE_URL, timeout=3)
    except requests.exceptions.ConnectionError:
        _fail(f"Impossible de joindre {BASE_URL}. Le serveur backend est-il lancé ?")
        return

    test_protected_route_without_token()

    # Ces deux tests consomment le quota de rate limiting — les lancer en dernier
    # évite de fausser les autres tests si le serveur mutualise un même compteur IP.
    test_forgot_password_rate_limit_and_enumeration()

    print(
        "\nPour tester le flux /auth/refresh, fournissez un compte existant et "
        "déjà vérifié (email + mot de passe) :"
    )
    test_email = input("  Email (laisser vide pour ignorer ce test) : ").strip()
    if test_email:
        test_password = input("  Mot de passe : ").strip()
        test_refresh_flow(test_email, test_password)
    else:
        _info("Test /auth/refresh ignoré (aucun email fourni).")

    print(
        "\nPour tester le rate limiting sur /auth/login et /auth/register, "
        "relancez ce script séparément en décommentant les appels ci-dessous "
        "(ils consomment un quota horaire et peuvent bloquer temporairement "
        "votre propre IP)."
    )
    run_heavy_tests = input("  Lancer aussi les tests /auth/login et /auth/register maintenant ? (o/N) : ").strip().lower()
    if run_heavy_tests == "o":
        test_login_rate_limit()
        test_register_rate_limit()

    _title("Terminé")
    print("Relisez les lignes [FAIL] ci-dessus si présentes — ce sont les points à corriger.")


if __name__ == "__main__":
    main()
