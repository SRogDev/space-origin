"""Deterministic simulation engine for SpaceOrigins.

The sim NEVER depends on an LLM: every tick is a pure function of
``(seed, tick_count, player actions)`` via ``random.Random(seed + tick_count)``.
Same seed + same actions  =>  identical world state, always.

Formulas are deliberately simple but interconnected: food <-> population <->
economy <-> resources <-> environment <-> values, with policies, technologies
and wiki-driven events perturbing the trajectory.
"""

from __future__ import annotations

import random
import uuid
from typing import Any

from api import content as wiki
from api import events as event_eval
from api.models import (
    START_YEAR,
    Colony,
    Game,
    GameEvent,
    HistoryEntry,
    SocietyValues,
)

VALUE_AXES = (
    "liberty_authority",
    "individualism_collectivism",
    "pacifism_militarism",
    "ecology_industrialism",
    "secular_spiritual",
)

PER_CAPITA_FOOD = 1.0  # food units consumed per person per year
BASE_BIRTH_RATE = 0.022
BASE_DEATH_RATE = 0.010
DEFAULT_EVENT_COOLDOWN = 5  # years between firings of the same event


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# Colony creation
# ---------------------------------------------------------------------------


def create_colony(name: str, values: dict[str, float], home_place_id: str, seed: int) -> Game:
    """Create a new game with sensible starting conditions."""
    missing = [ax for ax in VALUE_AXES if ax not in values]
    if missing:
        raise ValueError(f"values missing axes: {missing}")
    try:
        axes = {ax: _clamp(float(values[ax]), -1.0, 1.0) for ax in VALUE_AXES}
    except (TypeError, ValueError) as e:
        raise ValueError(f"values must be numeric: {e}") from e

    game_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"spaceorigins:{seed}"))
    game = Game(
        id=game_id,
        seed=int(seed),
        year=START_YEAR,
        colony=Colony(name=name, place_id=home_place_id, founded_year=START_YEAR),
        values=SocietyValues(**axes),
    )
    # food_stock default (20_000) already covers ~2 years for 10_000 people
    game.history.append(
        HistoryEntry(
            year=START_YEAR,
            text=(
                f"{START_YEAR}: Colony '{name}' founded at {home_place_id} by charter "
                f"corporation. Population 10,000. Treasury 1,000,000 credits."
            ),
        )
    )
    return game


# ---------------------------------------------------------------------------
# Tick engine
# ---------------------------------------------------------------------------


def advance_time(game: Game, years: int) -> Game:
    """Advance the simulation ``years`` ticks. Mutates in place, returns game."""
    if not isinstance(years, int) or years < 1:
        raise ValueError("years must be a positive integer")
    for _ in range(years):
        game.year += 1
        rng = random.Random(game.seed + game.tick_count)
        _tick(game, rng)
        game.tick_count += 1
        _append_compact_history(game)
    return game


def _tick(game: Game, rng: random.Random) -> None:
    pop, eco, res, gov, vals = (
        game.population,
        game.economy,
        game.resources,
        game.government,
        game.values,
    )
    env, tech, mil = game.environment, game.technology, game.military

    industrialism = max(0.0, vals.ecology_industrialism)  # 0..1
    ecology = max(0.0, -vals.ecology_industrialism)  # 0..1
    depletion_factor = (0.5 + industrialism) * (1.0 - 0.5 * ecology)

    # --- food ----------------------------------------------------------
    food_prod = pop.size * pop.employment * pop.productivity * env.habitability * 1.75
    need = pop.size * PER_CAPITA_FOOD
    available = res.food_stock + food_prod
    if available < need:
        shortage = 1.0 - available / need
        res.food_stock = 0.0
    else:
        shortage = 0.0
        res.food_stock = min(available - need, need * 20)  # storage cap: 20 years
    res.food_production = food_prod
    res.food_consumption = need

    # --- population ----------------------------------------------------
    birth_eff = pop.birth_rate * (0.4 + 0.6 * pop.living_conditions) * (0.5 + 0.5 * pop.health)
    death_eff = pop.death_rate * (1.6 - pop.health) * (1.0 + 2.5 * shortage)
    births = pop.size * birth_eff
    deaths = pop.size * death_eff
    migration = rng.uniform(-0.002, 0.004) * pop.size * (0.3 + 0.7 * pop.satisfaction)
    pop.size = _clamp(pop.size + births - deaths + migration, 100, 10_000_000)
    pop.growth_rate = (births - deaths + migration) / max(pop.size, 1)
    pop.birth_rate = _clamp(pop.birth_rate + (BASE_BIRTH_RATE - pop.birth_rate) * 0.05, 0.001, 0.06)
    pop.death_rate = _clamp(pop.death_rate + (BASE_DEATH_RATE - pop.death_rate) * 0.05, 0.001, 0.06)

    target_emp = 0.88 - pop.unrest * 0.15 - shortage * 0.2
    pop.employment = _clamp(
        pop.employment + _clamp(target_emp - pop.employment, -0.05, 0.05), 0.3, 0.98
    )

    wealth = eco.treasury / max(pop.size, 1)
    pop.wealth_per_capita = _clamp(wealth, 0, 1e9)
    living_target = (
        0.35 * (1.0 - shortage)
        + 0.35 * min(1.0, wealth / 2000)
        + 0.2 * (1.0 - env.pollution)
        + 0.1 * pop.health
    )
    pop.living_conditions = _clamp(
        pop.living_conditions + (living_target - pop.living_conditions) * 0.2, 0, 1
    )

    sat_target = _clamp(
        0.3 + 0.5 * pop.living_conditions - 0.3 * shortage - 0.5 * max(0.0, eco.tax_rate - 0.3),
        0,
        1,
    )
    pop.satisfaction = _clamp(pop.satisfaction + (sat_target - pop.satisfaction) * 0.25, 0, 1)
    unrest_target = _clamp((1.0 - pop.satisfaction) * 0.8 + shortage * 0.2, 0, 1)
    pop.unrest = _clamp(
        pop.unrest + (unrest_target - pop.unrest) * 0.2 + rng.uniform(-0.01, 0.01), 0, 1
    )
    pop.health = _clamp(
        pop.health + ((0.5 + 0.5 * pop.living_conditions) - pop.health) * 0.03, 0, 1
    )
    pop.education = _clamp(
        pop.education + _clamp(eco.investment_rate * 0.05 - 0.005, -0.01, 0.02), 0, 1
    )

    # --- economy -------------------------------------------------------
    labor = pop.size * pop.employment
    energy_demand = labor * 0.001
    energy_factor = _clamp(eco.energy_production / max(energy_demand, 1e-9), 0.25, 1.0)
    eco.production = labor * pop.productivity * energy_factor
    eco.consumption = pop.size * 0.9 + eco.production * 0.05

    revenue = eco.production * eco.tax_rate
    invest_amt = eco.production * eco.investment_rate
    pop.productivity = _clamp(
        pop.productivity * (1.0 + 0.03 * eco.investment_rate * (0.5 + pop.education)), 0.1, 20.0
    )
    military_cost = eco.production * mil.spending_share * 0.5
    eco.treasury = _clamp(
        eco.treasury
        + revenue
        - invest_amt
        - military_cost
        + (eco.production - eco.consumption) * 0.05,
        -1e12,
        1e15,
    )
    eco.gdp_proxy = eco.production
    res.energy_stock = _clamp(
        res.energy_stock + eco.energy_production - energy_demand, 0, eco.energy_production * 5 + 1
    )

    # --- resources -----------------------------------------------------
    res.metals = max(0.0, res.metals - eco.production * 0.0002 * depletion_factor)
    res.water_ice = max(0.0, res.water_ice - pop.size * 0.00005 * depletion_factor)

    # --- environment ---------------------------------------------------
    env.pollution = _clamp(
        env.pollution + eco.production * 2e-7 * depletion_factor - env.pollution * 0.01, 0, 1
    )
    env.habitability = _clamp(0.75 - env.pollution * 0.4, 0.1, 1.0)

    # --- technology: research points accrue; research itself is player-driven
    tech.research_points += (
        (pop.size / 1000) * (0.5 + pop.education) * (0.2 + eco.investment_rate) * 5
    )

    # --- military ------------------------------------------------------
    mil.strength = _clamp(
        mil.strength + eco.production * mil.spending_share * 0.001 - mil.strength * 0.01, 0, 1e9
    )

    # --- government ----------------------------------------------------
    stab_target = _clamp(0.8 - pop.unrest * 0.4 - shortage * 0.2, 0, 1)
    gov.stability = _clamp(gov.stability + (stab_target - gov.stability) * 0.1, 0, 1)

    # --- values drift toward active policies ---------------------------
    for pid in game.active_policies:
        try:
            policy = wiki.get_content("policies", pid)
        except KeyError:
            continue
        for axis, delta in (policy["meta"].get("value_shift") or {}).items():
            if axis in VALUE_AXES:
                setattr(vals, axis, _clamp(getattr(vals, axis) + float(delta) * 0.05, -1, 1))
    for axis in VALUE_AXES:  # extremes soften slowly without reinforcement
        setattr(vals, axis, getattr(vals, axis) * 0.999)

    # --- events --------------------------------------------------------
    _evaluate_events(game, rng)


def _append_compact_history(game: Game) -> None:
    game.history.append(
        HistoryEntry(
            year=game.year,
            text=(
                f"{game.year}: pop {game.population.size:,.0f} "
                f"(growth {game.population.growth_rate:+.1%}), "
                f"treasury {game.economy.treasury:,.0f}, "
                f"food {game.resources.food_stock:,.0f}, "
                f"satisfaction {game.population.satisfaction:.2f}, "
                f"unrest {game.population.unrest:.2f}."
            ),
        )
    )


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


def _evaluate_events(game: Game, rng: random.Random) -> None:
    for event in wiki.list_content("events"):
        meta = event["meta"]
        triggers = meta.get("triggers") or []
        if not triggers:
            continue
        if not all(event_eval.evaluate_trigger(game, t) for t in triggers):
            continue
        cooldown = int(meta.get("cooldown", DEFAULT_EVENT_COOLDOWN))
        last_fired = max((e.year for e in game.events_fired if e.id == event["id"]), default=None)
        if last_fired is not None and game.year - last_fired < cooldown:
            continue
        if rng.random() >= float(meta.get("weight", 0.5)):
            continue
        _fire_event(game, event)


def _fire_event(game: Game, event: dict[str, Any]) -> None:
    meta = event["meta"]
    for path, delta in (meta.get("state_changes") or {}).items():
        try:
            wiki.apply_modifier(game, str(path), delta, mode="additive")
        except ValueError:
            continue  # a bad path in content never breaks the sim
    consequences = meta.get("consequences") or {}
    summary = (
        "; ".join(f"{k}: {v}" for k, v in consequences.items() if isinstance(v, str))
        or "unrecorded consequences"
    )
    game.events_fired.append(
        GameEvent(
            id=event["id"], year=game.year, name=meta.get("name", event["id"]), summary=summary
        )
    )
    game.history.append(
        HistoryEntry(
            year=game.year, text=f"{game.year}: EVENT — {meta.get('name', event['id'])}: {summary}."
        )
    )


# ---------------------------------------------------------------------------
# Player actions: policies & research
# ---------------------------------------------------------------------------


def _resolve_tech_id(ref: Any) -> str:
    """'[[technologies/fusion-power]]' -> 'fusion-power'; plain ids pass through."""
    s = str(ref).strip()
    if s.startswith("[[") and s.endswith("]]"):
        inner = s[2:-2]
        return inner.split("/")[-1]
    return s


def apply_policy(game: Game, policy_id: str) -> Game:
    """Enact a policy: value_shift + one-time modifiers. Unknown id -> ValueError."""
    try:
        policy = wiki.get_content("policies", policy_id)
    except KeyError as e:
        raise ValueError(f"unknown policy: {policy_id!r}") from e
    if policy_id in game.active_policies:
        raise ValueError(f"policy already active: {policy_id!r}")
    meta = policy["meta"]

    # requirements: technology ids (plain or [[technologies/id]]) must be researched
    for req in meta.get("requirements") or []:
        tid = _resolve_tech_id(req)
        if tid not in game.technology.researched:
            raise ValueError(f"policy {policy_id!r} requires technology {tid!r}")

    for axis, delta in (meta.get("value_shift") or {}).items():
        if axis in VALUE_AXES:
            current = getattr(game.values, axis)
            setattr(game.values, axis, _clamp(current + float(delta), -1, 1))
    for path, delta in (meta.get("modifiers") or {}).items():
        wiki.apply_modifier(game, str(path), delta, mode="additive")

    game.active_policies.append(policy_id)
    game.history.append(
        HistoryEntry(
            year=game.year,
            text=f"{game.year}: Policy enacted — {meta.get('name', policy_id)}.",
        )
    )
    return game


def research_technology(game: Game, tech_id: str) -> Game:
    """Research a technology: pay cost, gain stat_modifiers. Unknown/unmet -> ValueError."""
    try:
        tech = wiki.get_content("technologies", tech_id)
    except KeyError as e:
        raise ValueError(f"unknown technology: {tech_id!r}") from e
    if tech_id in game.technology.researched:
        raise ValueError(f"technology already researched: {tech_id!r}")
    meta = tech["meta"]

    for pre in meta.get("prerequisites") or []:
        pid = _resolve_tech_id(pre)
        if pid not in game.technology.researched:
            raise ValueError(f"technology {tech_id!r} requires {pid!r}")
    cost = float(meta.get("cost", 0))
    if game.technology.research_points < cost:
        raise ValueError(
            f"insufficient research points for {tech_id!r}: "
            f"need {cost:g}, have {game.technology.research_points:g}"
        )
    game.technology.research_points -= cost
    game.technology.researched.append(tech_id)
    for path, delta in (meta.get("stat_modifiers") or {}).items():
        wiki.apply_modifier(game, str(path), delta, mode="multiplicative")

    game.history.append(
        HistoryEntry(
            year=game.year,
            text=f"{game.year}: Technology researched — {meta.get('name', tech_id)}.",
        )
    )
    return game
