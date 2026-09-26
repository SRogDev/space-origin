"""RED phase: sim tests written before implementation.

Run: python -m pytest api/tests/test_sim.py -q  (expect collection/import failures)
"""

import math
import time

import pytest

from api import sim
from api.models import Game, game_fingerprint


def neutral_values():
    return {
        "liberty_authority": 0.0,
        "individualism_collectivism": 0.0,
        "pacifism_militarism": 0.0,
        "ecology_industrialism": 0.0,
        "secular_spiritual": 0.0,
    }


def iter_floats(obj):
    """Yield every float found in a pydantic model tree."""
    if isinstance(obj, float):
        yield obj
    elif hasattr(obj, "model_dump"):
        for v in obj.model_dump().values():
            yield from iter_floats(v)
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from iter_floats(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from iter_floats(v)


def test_create_colony_defaults():
    g = sim.create_colony("New Dawn", neutral_values(), "kepler-verge", seed=42)
    assert isinstance(g, Game)
    assert g.year == 2280
    assert g.tick_count == 0
    assert g.seed == 42
    assert g.colony.name == "New Dawn"
    assert g.colony.place_id == "kepler-verge"
    assert g.colony.founded_year == 2280
    assert g.population.size == 10_000
    assert g.economy.treasury == 1_000_000
    # ~2 years of food stock: size * per_capita(1.0) * 2
    assert g.resources.food_stock == pytest.approx(20_000, rel=0.05)
    assert g.technology.researched == []
    assert g.active_policies == []
    assert len(g.history) >= 1  # founding logged


def test_create_colony_rejects_bad_values():
    with pytest.raises(ValueError):
        sim.create_colony("X", {"liberty_authority": 0.0}, "kepler-verge", seed=1)


def test_advance_10_years_plausible():
    g = sim.create_colony("New Dawn", neutral_values(), "kepler-verge", seed=42)
    g = sim.advance_time(g, 10)
    assert g.year == 2290
    assert g.tick_count == 10
    # with food surplus and default birth > death, population grows
    assert g.population.size > 10_000
    assert g.economy.production > 0
    assert len(g.history) >= 11  # founding + one compact entry per tick
    for f in iter_floats(g):
        assert not math.isnan(f), "NaN found in game state"


def test_industrial_policy_tradeoff():
    g = sim.create_colony("New Dawn", neutral_values(), "kepler-verge", seed=42)
    treasury_before = g.economy.treasury
    axis_before = g.values.individualism_collectivism
    sim.apply_policy(g, "frontier-homestead-act")
    assert "frontier-homestead-act" in g.active_policies
    # value_shift: individualism_collectivism -0.2 (toward individualism)
    assert g.values.individualism_collectivism < axis_before
    assert g.values.individualism_collectivism == pytest.approx(axis_before - 0.2)
    # modifiers: treasury cost applied once
    assert g.economy.treasury < treasury_before
    with pytest.raises(ValueError):
        sim.apply_policy(g, "frontier-homestead-act")  # already active
    with pytest.raises(ValueError):
        sim.apply_policy(g, "no-such-policy")  # unknown -> ValueError (API maps to 404)


def test_research_gating():
    g = sim.create_colony("New Dawn", neutral_values(), "kepler-verge", seed=42)
    # cost gate: 0 research points cannot afford fission-power (cost 100)
    with pytest.raises(ValueError):
        sim.research_technology(g, "fission-power")
    with pytest.raises(ValueError):
        sim.research_technology(g, "no-such-tech")
    # prerequisite gate (monkeypatched fake tech, no wiki pollution)
    import api.content as content

    real_get = content.get_content

    def fake_get(ctype, cid):
        if ctype == "technologies" and cid == "fake-advanced":
            return {
                "id": "fake-advanced",
                "meta": {
                    "id": "fake-advanced",
                    "name": "Fake Advanced",
                    "prerequisites": ["fission-power"],
                    "cost": 10,
                },
                "body": "",
            }
        return real_get(ctype, cid)

    content.get_content = fake_get
    try:
        g.technology.research_points = 1000
        with pytest.raises(ValueError):
            sim.research_technology(g, "fake-advanced")  # prereq not researched
    finally:
        content.get_content = real_get
    # grant points -> research works, stat_modifiers applied
    energy_before = g.economy.energy_production
    sim.research_technology(g, "fission-power")
    assert "fission-power" in g.technology.researched
    assert g.technology.research_points == pytest.approx(1000 - 100)
    assert g.economy.energy_production > energy_before  # +50% multiplicative


def test_determinism():
    def play(seed):
        g = sim.create_colony("New Dawn", neutral_values(), "kepler-verge", seed=seed)
        sim.apply_policy(g, "frontier-homestead-act")
        g.technology.research_points = 500
        sim.research_technology(g, "fission-power")
        return sim.advance_time(g, 20)

    fp1 = game_fingerprint(play(7))
    fp2 = game_fingerprint(play(7))
    assert fp1 == fp2
    assert fp1 != game_fingerprint(play(8))  # different seed -> different trajectory


def test_soak_100_years():
    g = sim.create_colony("New Dawn", neutral_values(), "kepler-verge", seed=42)
    start = time.time()
    sim.advance_time(g, 100)
    elapsed = time.time() - start
    assert elapsed < 30, f"100-year soak took {elapsed:.1f}s"
    assert g.year == 2380
    for f in iter_floats(g):
        assert math.isfinite(f), "non-finite float after 100-year soak"
    assert 100 <= g.population.size <= 10_000_000
    assert g.economy.treasury >= -1e12


def test_event_fires():
    # solar-flare triggers on "year > 2280"; seed 1234 fires on the first tick
    g = sim.create_colony("New Dawn", neutral_values(), "kepler-verge", seed=1234)
    sim.advance_time(g, 1)
    assert g.year == 2281
    fired_ids = [e.id for e in g.events_fired]
    assert "solar-flare" in fired_ids
    assert any("Solar Flare" in h.text or "solar" in h.text.lower() for h in g.history)
