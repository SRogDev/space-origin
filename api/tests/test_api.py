"""API endpoint tests (FastAPI TestClient)."""

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)

VALUES = {
    "liberty_authority": 0.0,
    "individualism_collectivism": 0.0,
    "pacifism_militarism": 0.0,
    "ecology_industrialism": 0.0,
    "secular_spiritual": 0.0,
}


def make_game(name="New Dawn", seed=42):
    r = client.post(
        "/api/games",
        json={"name": name, "values": VALUES, "home_place_id": "kepler-verge", "seed": seed},
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_create_and_get_game():
    g = make_game()
    assert g["year"] == 2280
    assert g["population"]["size"] == 10_000
    r = client.get(f"/api/games/{g['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == g["id"]
    assert client.get("/api/games/nope").status_code == 404


def test_advance_validation_and_effect():
    g = make_game(seed=11)
    r = client.post(f"/api/games/{g['id']}/advance", json={"years": 5})
    assert r.status_code == 200
    assert r.json()["year"] == 2285
    assert r.json()["tick_count"] == 5
    assert client.post(f"/api/games/{g['id']}/advance", json={"years": 0}).status_code == 422
    assert client.post(f"/api/games/{g['id']}/advance", json={"years": 1001}).status_code == 422


def test_policy_endpoints():
    g = make_game(seed=12)
    r = client.post(f"/api/games/{g['id']}/policy", json={"policy_id": "frontier-homestead-act"})
    assert r.status_code == 200, r.text
    assert "frontier-homestead-act" in r.json()["active_policies"]
    r = client.post(f"/api/games/{g['id']}/policy", json={"policy_id": "no-such-policy"})
    assert r.status_code == 404


def test_research_endpoints():
    g = make_game(seed=13)
    # no research points yet -> 400 (gating), unknown tech -> 404
    r = client.post(f"/api/games/{g['id']}/research", json={"tech_id": "fission-power"})
    assert r.status_code == 400
    r = client.post(f"/api/games/{g['id']}/research", json={"tech_id": "no-such-tech"})
    assert r.status_code == 404


def test_content_endpoints():
    r = client.get("/api/content/technologies")
    assert r.status_code == 200
    assert any(i["id"] == "fission-power" for i in r.json())
    r = client.get("/api/content/policies/frontier-homestead-act")
    assert r.status_code == 200
    assert r.json()["meta"]["name"] == "Frontier Homestead Act"
    assert client.get("/api/content/nope").status_code == 404
    assert client.get("/api/content/events/nope").status_code == 404


def test_save_and_load():
    g = make_game(seed=14)
    client.post(f"/api/games/{g['id']}/advance", json={"years": 3})
    r = client.post(f"/api/games/{g['id']}/save", json={"name": "test-save"})
    assert r.status_code == 200, r.text
    r = client.get("/api/saves")
    assert r.status_code == 200
    assert "test-save" in r.json()
    r = client.post("/api/saves/test-save/load")
    assert r.status_code == 200
    assert r.json()["year"] == 2283
    assert client.post("/api/saves/nope/load").status_code == 404


def test_narrate_fallback_without_key():
    g = make_game(seed=15)
    r = client.post(f"/api/games/{g['id']}/narrate")
    assert r.status_code == 200
    text = r.json()["text"]
    assert isinstance(text, str) and len(text) > 0
    assert "2280" in text  # fallback bulletin carries the facts, no invented numbers
