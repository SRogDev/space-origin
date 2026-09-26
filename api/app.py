"""FastAPI surface for the SpaceOrigins game core.

All simulation logic lives in ``api.sim``; this module only validates input at
the boundary, keeps an in-memory game store, and maps sim errors to HTTP codes.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api import sim
from api.ai import narrator
from api.content import get_content, list_content
from api.models import Game

SAVES_DIR = Path(__file__).resolve().parent / "saves"
_SAVE_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")

app = FastAPI(title="SpaceOrigins — game core", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

games: dict[str, Game] = {}


# ---------------------------------------------------------------------------
# Request models (input validation at the API boundary)
# ---------------------------------------------------------------------------


class ValuesInput(BaseModel):
    liberty_authority: float = Field(ge=-1, le=1)
    individualism_collectivism: float = Field(ge=-1, le=1)
    pacifism_militarism: float = Field(ge=-1, le=1)
    ecology_industrialism: float = Field(ge=-1, le=1)
    secular_spiritual: float = Field(ge=-1, le=1)


class CreateGameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    values: ValuesInput
    home_place_id: str = Field(min_length=1, max_length=100)
    seed: int


class AdvanceRequest(BaseModel):
    years: int = Field(ge=1, le=1000)


class PolicyRequest(BaseModel):
    policy_id: str = Field(min_length=1, max_length=100)


class ResearchRequest(BaseModel):
    tech_id: str = Field(min_length=1, max_length=100)


class SaveRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_game(game_id: str) -> Game:
    game = games.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail=f"unknown game: {game_id!r}")
    return game


def _sim_error(exc: ValueError) -> HTTPException:
    # sim raises ValueError("unknown ...") for missing ids -> 404, else 400
    if str(exc).startswith("unknown "):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


def _check_save_name(name: str) -> None:
    if not _SAVE_NAME_RE.fullmatch(name):
        raise HTTPException(status_code=400, detail=f"invalid save name: {name!r}")


def _narrate_delta(game: Game) -> dict[str, Any]:
    """Build the read-only plain-data delta the narrator is allowed to see."""
    return {
        "year": game.year,
        "colony": game.colony.name,
        "population": round(game.population.size),
        "satisfaction": round(game.population.satisfaction, 2),
        "unrest": round(game.population.unrest, 2),
        "treasury": round(game.economy.treasury),
        "recent_events": [e.name for e in game.events_fired[-3:]],
        "latest": game.history[-1].text if game.history else "",
    }


# ---------------------------------------------------------------------------
# Games
# ---------------------------------------------------------------------------


@app.post("/api/games", response_model=Game)
def create_game(req: CreateGameRequest) -> Game:
    try:
        game = sim.create_colony(req.name, req.values.model_dump(), req.home_place_id, req.seed)
    except ValueError as exc:
        raise _sim_error(exc) from exc
    games[game.id] = game
    return game


@app.get("/api/games/{game_id}", response_model=Game)
def get_game(game_id: str) -> Game:
    return _get_game(game_id)


@app.post("/api/games/{game_id}/advance", response_model=Game)
def advance_game(game_id: str, req: AdvanceRequest) -> Game:
    game = _get_game(game_id)
    try:
        return sim.advance_time(game, req.years)
    except ValueError as exc:
        raise _sim_error(exc) from exc


@app.post("/api/games/{game_id}/policy", response_model=Game)
def apply_policy(game_id: str, req: PolicyRequest) -> Game:
    game = _get_game(game_id)
    try:
        return sim.apply_policy(game, req.policy_id)
    except ValueError as exc:
        raise _sim_error(exc) from exc


@app.post("/api/games/{game_id}/research", response_model=Game)
def research_technology(game_id: str, req: ResearchRequest) -> Game:
    game = _get_game(game_id)
    try:
        return sim.research_technology(game, req.tech_id)
    except ValueError as exc:
        raise _sim_error(exc) from exc


@app.post("/api/games/{game_id}/narrate")
def narrate_game(game_id: str) -> dict[str, str]:
    game = _get_game(game_id)
    return {"text": narrator.narrate(_narrate_delta(game))}


# ---------------------------------------------------------------------------
# Saves (JSON files under api/saves/)
# ---------------------------------------------------------------------------


@app.post("/api/games/{game_id}/save")
def save_game(game_id: str, req: SaveRequest) -> dict[str, str]:
    game = _get_game(game_id)
    _check_save_name(req.name)
    SAVES_DIR.mkdir(parents=True, exist_ok=True)
    (SAVES_DIR / f"{req.name}.json").write_text(game.model_dump_json(indent=2), encoding="utf-8")
    return {"saved": req.name, "game_id": game.id}


@app.get("/api/saves")
def list_saves() -> list[str]:
    if not SAVES_DIR.is_dir():
        return []
    return sorted(p.stem for p in SAVES_DIR.glob("*.json"))


@app.post("/api/saves/{name}/load", response_model=Game)
def load_save(name: str) -> Game:
    _check_save_name(name)
    path = SAVES_DIR / f"{name}.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"unknown save: {name!r}")
    game = Game.model_validate_json(path.read_text(encoding="utf-8"))
    games[game.id] = game
    return game


# ---------------------------------------------------------------------------
# Wiki content
# ---------------------------------------------------------------------------


@app.get("/api/content/{ctype}")
def list_wiki_content(ctype: str) -> list[dict[str, Any]]:
    try:
        return list_content(ctype)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/content/{ctype}/{cid}")
def get_wiki_content(ctype: str, cid: str) -> dict[str, Any]:
    try:
        return get_content(ctype, cid)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
