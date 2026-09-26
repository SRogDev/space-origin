"""Tests for the wiki content loader."""

import pytest

from api import content


def test_list_technologies():
    items = content.list_content("technologies")
    ids = [i["id"] for i in items]
    assert "fission-power" in ids
    item = next(i for i in items if i["id"] == "fission-power")
    assert item["meta"]["name"] == "Fission Power"
    assert item["body"].strip() != ""


def test_get_policy():
    item = content.get_content("policies", "frontier-homestead-act")
    assert item["meta"]["name"] == "Frontier Homestead Act"
    assert item["meta"]["value_shift"]["individualism_collectivism"] == -0.2


def test_unknown_type_and_id():
    with pytest.raises(ValueError):
        content.list_content("starships")
    with pytest.raises(KeyError):
        content.get_content("events", "no-such-event")


def test_templates_are_skipped():
    for ctype in ("technologies", "policies", "events", "places", "lore"):
        ids = [i["id"] for i in content.list_content(ctype)]
        assert not any(i.startswith("_") for i in ids)


def test_modifier_path_whitelist_derived_from_models():
    paths = content.MODIFIABLE_PATHS
    assert "population.satisfaction" in paths
    assert "economy.treasury" in paths
    assert "economy.energy_production" in paths
    assert "values.liberty_authority" in paths
    # no string/list fields leak into the whitelist
    assert not any(p.endswith(".name") for p in paths)
    assert not any("researched" in p for p in paths)
