import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Nominatim exige un User-Agent identifiable (politique d'usage du service gratuit)
HEADERS = {"User-Agent": "TripMatch/1.0 (contact: matrixbeji1@gmail.com)"}


def geocode_city(city_name: str) -> tuple[float, float] | None:
    """
    Convertit un nom de ville en coordonnées GPS (latitude, longitude) via Nominatim.
    Retourne None si la ville n'est pas trouvée ou en cas d'erreur réseau.
    """
    params = {
        "q": f"{city_name}, Tunisia",
        "format": "json",
        "limit": 1,
    }

    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=5)
        response.raise_for_status()
        results = response.json()

        if not results:
            return None

        lat = float(results[0]["lat"])
        lon = float(results[0]["lon"])
        return (lat, lon)

    except (requests.RequestException, KeyError, ValueError, IndexError):
        return None