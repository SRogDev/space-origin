"""Pydantic v2 world-state models for SpaceOrigins.

Every model is JSON-serializable (round-trip safe). The simulation mutates these
in place; ``game_fingerprint`` gives a canonical hash so determinism is testable:
same seed + same actions  =>  identical fingerprint.
"""

from __future__ import annotations

import hashlib
import json
from typing import Optional

from pydantic import BaseModel, Field

START_YEAR = 2280


class Population(BaseModel):
    size: float = Field(default=10_000, ge=0)
    growth_rate: float = 0.012
    birth_rate: float = Field(default=0.022, ge=0, le=1)
    death_rate: float = Field(default=0.010, ge=0, le=1)
    employment: float = Field(default=0.82, ge=0, le=1)
    productivity: float = Field(default=1.0, ge=0)
    wealth_per_capita: float = Field(default=1000.0, ge=0)
    satisfaction: float = Field(default=0.6, ge=0, le=1)
    unrest: float = Field(default=0.1, ge=0, le=1)
    education: float = Field(default=0.5, ge=0, le=1)
    health: float = Field(default=0.7, ge=0, le=1)
    living_conditions: float = Field(default=0.6, ge=0, le=1)


class Economy(BaseModel):
    treasury: float = 1_000_000
    production: float = Field(default=0.0, ge=0)
    consumption: float = Field(default=0.0, ge=0)
    tax_rate: float = Field(default=0.25, ge=0, le=1)
    investment_rate: float = Field(default=0.2, ge=0, le=1)
    energy_production: float = Field(default=10.0, ge=0)
    gdp_proxy: float = Field(default=0.0, ge=0)


class Resources(BaseModel):
    food_stock: float = Field(default=20_000, ge=0)
    food_production: float = Field(default=0.0, ge=0)
    food_consumption: float = Field(default=0.0, ge=0)
    metals: float = Field(default=1_000_000, ge=0)
    water_ice: float = Field(default=500_000, ge=0)
    energy_stock: float = Field(default=0.0, ge=0)


class Government(BaseModel):
    authority_structure: str = "corporate-charter"
    stability: float = Field(default=0.7, ge=0, le=1)


class SocietyValues(BaseModel):
    liberty_authority: float = Field(default=0.0, ge=-1, le=1)
    individualism_collectivism: float = Field(default=0.0, ge=-1, le=1)
    pacifism_militarism: float = Field(default=0.0, ge=-1, le=1)
    ecology_industrialism: float = Field(default=0.0, ge=-1, le=1)
    secular_spiritual: float = Field(default=0.0, ge=-1, le=1)


class TechnologyState(BaseModel):
    researched: list[str] = Field(default_factory=list)
    research_points: float = Field(default=0.0, ge=0)
    current_focus: Optional[str] = None


class Military(BaseModel):
    strength: float = Field(default=100.0, ge=0)
    spending_share: float = Field(default=0.1, ge=0, le=1)


class Environment(BaseModel):
    pollution: float = Field(default=0.05, ge=0, le=1)
    habitability: float = Field(default=0.7, ge=0, le=1)


class GameEvent(BaseModel):
    id: str
    year: int
    name: str
    summary: str


class HistoryEntry(BaseModel):
    year: int
    text: str


class Colony(BaseModel):
    name: str
    place_id: str
    founded_year: int = START_YEAR


class Game(BaseModel):
    id: str
    seed: int
    year: int = START_YEAR
    colony: Colony
    population: Population = Field(default_factory=Population)
    economy: Economy = Field(default_factory=Economy)
    resources: Resources = Field(default_factory=Resources)
    government: Government = Field(default_factory=Government)
    values: SocietyValues = Field(default_factory=SocietyValues)
    technology: TechnologyState = Field(default_factory=TechnologyState)
    military: Military = Field(default_factory=Military)
    environment: Environment = Field(default_factory=Environment)
    active_policies: list[str] = Field(default_factory=list)
    events_fired: list[GameEvent] = Field(default_factory=list)
    history: list[HistoryEntry] = Field(default_factory=list)
    tick_count: int = Field(default=0, ge=0)


def game_fingerprint(game: Game) -> str:
    """Canonical SHA-256 hash of the game state.

    Deterministic: the same seed + the same actions always produce the same
    fingerprint, which is how the test-suite proves the sim is deterministic.
    """
    canonical = json.dumps(game.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
