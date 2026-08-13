import requests

from app.core.config import settings


def _send_smtp_email(to_email: str, subject: str, html_body: str) -> None:
    """Envoie un email via l'API HTTP de Brevo (le SMTP sortant est bloqué sur Railway)."""
    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "accept": "application/json",
            "api-key": settings.BREVO_API_KEY,
            "content-type": "application/json",
        },
        json={
            "sender": {
                "name": settings.BREVO_SENDER_NAME,
                "email": settings.BREVO_SENDER_EMAIL,
            },
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_body,
        },
        timeout=10,
    )
    response.raise_for_status()


def send_verification_email(to_email: str, token: str) -> None:
    """Envoie l'email de vérification de compte (US-02)."""
    link = f"{settings.FRONTEND_URL}/auth/verify-email?token={token}"

    if settings.EMAIL_PROVIDER == "console":
        print("=" * 60)
        print(f"[EMAIL SIMULÉ] Vérification de compte pour {to_email}")
        print(f"Lien de vérification : {link}")
        print(f"Expire dans {settings.EMAIL_VERIFICATION_EXPIRE_HOURS}h")
        print("=" * 60)
        return

    if settings.EMAIL_PROVIDER == "brevo":
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto;">
            <h2 style="color: #2A4B9B;">Bienvenue sur TripMatch !</h2>
            <p>Merci de vous être inscrit. Cliquez sur le lien ci-dessous pour vérifier votre compte :</p>
            <p><a href="{link}" style="background: #2A4B9B; color: white; padding: 12px 24px;
               text-decoration: none; border-radius: 8px; display: inline-block;">
               Vérifier mon compte</a></p>
            <p style="color: #888; font-size: 13px;">Ce lien expire dans {settings.EMAIL_VERIFICATION_EXPIRE_HOURS}h.</p>
        </div>
        """
        _send_smtp_email(to_email, "Vérifiez votre compte TripMatch", html_body)
        return

    raise NotImplementedError(f"Provider email inconnu : {settings.EMAIL_PROVIDER}")


def send_password_reset_email(to_email: str, token: str) -> None:
    """Envoie l'email de réinitialisation de mot de passe (US-04)."""
    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    if settings.EMAIL_PROVIDER == "console":
        print("=" * 60)
        print(f"[EMAIL SIMULÉ] Réinitialisation du mot de passe pour {to_email}")
        print(f"Lien de réinitialisation : {link}")
        print(f"Expire dans {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes")
        print("=" * 60)
        return

    if settings.EMAIL_PROVIDER == "brevo":
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto;">
            <h2 style="color: #2A4B9B;">Réinitialisation de votre mot de passe</h2>
            <p>Cliquez sur le lien ci-dessous pour choisir un nouveau mot de passe :</p>
            <p><a href="{link}" style="background: #2A4B9B; color: white; padding: 12px 24px;
               text-decoration: none; border-radius: 8px; display: inline-block;">
               Réinitialiser mon mot de passe</a></p>
            <p style="color: #888; font-size: 13px;">Ce lien expire dans {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes.</p>
        </div>
        """
        _send_smtp_email(to_email, "Réinitialisation de votre mot de passe TripMatch", html_body)
        return

    raise NotImplementedError(f"Provider email inconnu : {settings.EMAIL_PROVIDER}")