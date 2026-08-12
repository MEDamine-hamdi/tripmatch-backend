import filetype

# Mapping entre les types MIME qu'on accepte et les extensions réelles
# détectées par analyse du contenu binaire (magic bytes), pas du header
# Content-Type envoyé par le client (falsifiable).
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


def validate_image_content(file_bytes: bytes) -> None:
    """Vérifie que le contenu binaire d'un fichier correspond réellement à
    une image autorisée, en inspectant ses magic bytes plutôt que le
    Content-Type déclaré par le client (qui peut être falsifié).

    Lève ValueError si le fichier n'est pas une image valide du type attendu.
    """
    kind = filetype.guess(file_bytes)

    if kind is None:
        raise ValueError(
            "Impossible de déterminer le type de fichier. "
            "Assurez-vous d'envoyer une vraie image JPEG, PNG ou WebP."
        )

    if kind.mime not in ALLOWED_IMAGE_MIME_TYPES:
        raise ValueError(
            f"Le contenu du fichier ne correspond pas à une image autorisée "
            f"(détecté : {kind.mime}). Utilisez JPEG, PNG ou WebP."
        )