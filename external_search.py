import requests

def search_google_books(query):
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": query,
        "maxResults": 5
    }

    try:
        r = requests.get(url, params=params, timeout=5)
        data = r.json()

        if "items" not in data:
            return None

        results = []
        for item in data["items"]:
            info = item.get("volumeInfo", {})
            results.append({
                "title": info.get("title"),
                "authors": info.get("authors", []),
                "confidence": 0.7  # heuristic confidence
            })

        return results

    except Exception:
        return None

def search_open_library(query):
    url = "https://openlibrary.org/search.json"
    params = {
        "q": query,
        "limit": 5
    }

    try:
        r = requests.get(url, params=params, timeout=5)
        data = r.json()

        if "docs" not in data:
            return None

        results = []
        for doc in data["docs"]:
            results.append({
                "title": doc.get("title"),
                "authors": doc.get("author_name", []),
                "confidence": 0.5  # lower than Google
            })

        return results

    except Exception:
        return None
