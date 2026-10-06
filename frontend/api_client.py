"""
Thin HTTP client for the FastAPI backend.

The frontend never imports backend modules directly — every interaction
goes through these functions, which turn network/HTTP failures into a
single ApiError with a message that's safe to show in the UI (no raw
tracebacks, no leaked stack traces).
"""

import requests

DEFAULT_TIMEOUT = 15
INGEST_TIMEOUT = 120  # scraping + embedding a page can take a while
CHAT_TIMEOUT = 60
DELETE_TIMEOUT = 30


class ApiError(Exception):
    """Raised for any backend or network failure. str(e) is safe to show the user."""
    pass


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, timeout: int, **kwargs):
        url = f"{self.base_url}{path}"
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
        except requests.exceptions.ConnectionError:
            raise ApiError(
                "Can't reach the backend. Is the FastAPI server running "
                f"at {self.base_url}?"
            )
        except requests.exceptions.Timeout:
            raise ApiError("The request timed out. The backend may be busy or unreachable.")
        except requests.exceptions.RequestException as e:
            raise ApiError(f"Request failed: {e}")

        if response.status_code >= 400:
            detail = None
            try:
                detail = response.json().get("detail")
            except ValueError:
                pass
            raise ApiError(detail or f"Backend returned HTTP {response.status_code}.")

        if not response.content:
            return None

        try:
            return response.json()
        except ValueError:
            raise ApiError("Backend returned an unexpected (non-JSON) response.")

    # --- sets -----------------------------------------------------------

    def list_sets(self):
        return self._request("GET", "/sets", DEFAULT_TIMEOUT)

    def create_set(self, name: str):
        return self._request("POST", "/sets", DEFAULT_TIMEOUT, json={"name": name})

    def delete_set(self, set_id: int):
        return self._request("DELETE", f"/sets/{set_id}", DELETE_TIMEOUT)

    def get_status(self, set_id: int):
        return self._request("GET", f"/sets/{set_id}/status", DEFAULT_TIMEOUT)

    # --- knowledge (ingested URLs) ---------------------------------------

    def list_knowledges(self, set_id: int):
        return self._request("GET", f"/sets/{set_id}/knowledges", DEFAULT_TIMEOUT)

    def ingest_url(self, set_id: int, url: str):
        return self._request(
            "POST", f"/sets/{set_id}/documents", INGEST_TIMEOUT, params={"url": url}
        )

    def get_messages(self, set_id: int):
        return self._request("GET", f"/sets/{set_id}/messages", DEFAULT_TIMEOUT)

    # --- chat -------------------------------------------------------------

    def send_chat(self, set_id: int, message: str):
        return self._request(
            "POST", f"/sets/{set_id}/chat", CHAT_TIMEOUT, json={"message": message}
        )
