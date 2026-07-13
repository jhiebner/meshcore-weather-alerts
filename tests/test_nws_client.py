from meshcore_weather.nws import Alert, fetch_active_alerts


def test_fetch_active_alerts_returns_payload_on_success(monkeypatch) -> None:
    class FakeResponse:
        def __init__(self, status_code: int, payload: dict) -> None:
            self.status_code = status_code
            self._payload = payload

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise RuntimeError("boom")

        def json(self) -> dict:
            return self._payload

    def fake_get(url: str, timeout: int = 10) -> FakeResponse:
        return FakeResponse(200, {"features": []})

    monkeypatch.setattr("meshcore_weather.nws.requests.get", fake_get)

    payload = fetch_active_alerts("https://example.test")

    assert payload == {"features": []}


def test_fetch_active_alerts_returns_empty_dict_on_error(monkeypatch) -> None:
    def fake_get(url: str, timeout: int = 10) -> object:
        raise RuntimeError("boom")

    monkeypatch.setattr("meshcore_weather.nws.requests.get", fake_get)

    payload = fetch_active_alerts("https://example.test")

    assert payload == {}
