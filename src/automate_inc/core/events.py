"""External pressure: events that get unlocked and then randomly triggered.

Built like ``core/tech.py`` on purpose - blueprint dataclass, registry loaded from
bundled JSON, cached loader - and the same core rule: **events never appear in
engine code.** ``core/tech.py`` folds everything researched into one ``Modifiers``
value object; this module folds everything currently running into one
``Pressure`` value object. The rest of the engine asks that object questions
("how high are fixed costs right now?") instead of knowing event IDs. A new
event that reuses an existing effect field is therefore pure configuration.

Two questions stay deliberately separate:

1. Is the event even possible? ``EventRegistry.is_available`` reads it
   deterministically off an ``EventContext`` built from the game state - the
   same idea as ``TechRegistry.is_available``.
2. Does it trigger this round? A roll against the pool of unlocked, not-yet-
   pending events, with the turn's derived RNG so save/load stays reproducible.
   That roll lives in ``core.game.Game._trigger_events``, not here.

An event that fires does not act on its own. It only opens a ``PendingDecision``
- the chosen ``EventOption`` is what carries effects, and only once the player
answers.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field, fields
from enum import Enum
from functools import lru_cache
from importlib import resources

INSTANT = 0
"""Sentinel duration: effects book once, immediately, when the option is chosen."""

PERMANENT = -1
"""Sentinel duration: effects run every round until the game ends."""


class EventCategory(str, Enum):
    AI = "AI"
    MARKET = "MARKET"
    PRIVATE = "PRIVATE"
    INVESTOR = "INVESTOR"


INSTANT_FIELDS = frozenset({"money", "research", "tokens", "alignment"})
"""Booked once, the moment an option is chosen - never read by ``Pressure``."""

RUNNING_FIELDS = frozenset(
    {"income_multiplier", "cost_multiplier", "fixed_cost", "cost_per_agent", "alignment_per_round"}
)
"""Read every round for as long as the option stays active."""


@dataclass(frozen=True)
class EventOption:
    """One answer to an event. Effects are homogeneous: an option is either an
    instant booking or a running pressure, never both - the same JSON shape as
    a technology's ``effects``, disambiguated by ``duration``."""

    id: str
    label: str
    effects: dict[str, float] = field(default_factory=dict)
    duration: int = INSTANT

    @property
    def is_instant(self) -> bool:
        return self.duration == INSTANT


@dataclass(frozen=True)
class Event:
    """A blueprint from data/events.json - unlocked, not yet triggered."""

    id: str
    category: EventCategory
    name: str
    description: str
    requires: dict[str, object]
    chance: float
    once: bool
    options: tuple[EventOption, ...]

    def option(self, option_id: str) -> EventOption | None:
        return next((o for o in self.options if o.id == option_id), None)


@dataclass(frozen=True)
class ActiveEffect:
    """A running ``EventOption`` currently in effect, as stored in ``GameState``."""

    event_id: str
    option_id: str
    remaining: int
    """Rounds left, aged down each turn. ``PERMANENT`` never ages."""

    def to_dict(self) -> dict:
        return {"event_id": self.event_id, "option_id": self.option_id, "remaining": self.remaining}

    @classmethod
    def from_dict(cls, data: dict) -> ActiveEffect:
        return cls(
            event_id=data["event_id"], option_id=data["option_id"], remaining=data["remaining"]
        )


@dataclass(frozen=True)
class Pressure:
    """Everything currently running, folded into one value object.

    Defaults are the neutral element of each field's aggregation rule, so no
    active events mean "no pressure at all" - exactly like an empty ``Modifiers``.
    """

    income_multiplier: float = 1.0
    cost_multiplier: float = 1.0
    fixed_cost: float = 0.0
    cost_per_agent: float = 0.0
    alignment_per_round: float = 0.0


PRESSURE_AGGREGATION: dict[str, str] = {
    "income_multiplier": "multiply",
    "cost_multiplier": "multiply",
    "fixed_cost": "add",
    "cost_per_agent": "add",
    "alignment_per_round": "add",
}

PRESSURE_FIELDS = frozenset(f.name for f in fields(Pressure))


def aggregate_pressure(options: Iterable[EventOption]) -> Pressure:
    """Fold every currently active option into a single ``Pressure``."""
    values: dict[str, float] = {f.name: f.default for f in fields(Pressure)}
    for option in options:
        for key, amount in option.effects.items():
            rule = PRESSURE_AGGREGATION[key]
            if rule == "multiply":
                values[key] *= amount
            else:
                values[key] += amount
    return Pressure(**values)


@dataclass(frozen=True)
class EventContext:
    """Everything ``requires`` conditions read, snapshotted once per turn.

    Built by ``Game`` from ``GameState`` and ``Modifiers`` - this module knows
    nothing about either type, the same separation ``tech.py`` keeps from
    ``GameState``.
    """

    turn: int
    money: float
    alignment: float
    unlocked_agent_level: int
    agents: int
    humans: int
    projects: int
    last_net: float | None
    triggered: frozenset[str]


def _cond_min_turn(ctx: EventContext, value: float) -> bool:
    return ctx.turn >= value


def _cond_every_n_turns(ctx: EventContext, value: float) -> bool:
    n = int(value)
    return n > 0 and ctx.turn % n == 0


def _cond_min_agents(ctx: EventContext, value: float) -> bool:
    return ctx.agents >= value


def _cond_min_humans(ctx: EventContext, value: float) -> bool:
    return ctx.humans >= value


def _cond_agents_outnumber_humans(ctx: EventContext, value: bool) -> bool:
    return (ctx.agents > ctx.humans) if value else True


def _cond_min_agent_level(ctx: EventContext, value: float) -> bool:
    return ctx.unlocked_agent_level >= value


def _cond_min_projects(ctx: EventContext, value: float) -> bool:
    return ctx.projects >= value


def _cond_min_alignment(ctx: EventContext, value: float) -> bool:
    return ctx.alignment >= value


def _cond_max_alignment(ctx: EventContext, value: float) -> bool:
    return ctx.alignment <= value


def _cond_min_money(ctx: EventContext, value: float) -> bool:
    return ctx.money >= value


def _cond_max_money(ctx: EventContext, value: float) -> bool:
    return ctx.money <= value


def _cond_max_last_net(ctx: EventContext, value: float) -> bool:
    return ctx.last_net is not None and ctx.last_net <= value


def _cond_after_event(ctx: EventContext, value: str) -> bool:
    return value in ctx.triggered


def _cond_not_after_event(ctx: EventContext, value: str) -> bool:
    return value not in ctx.triggered


CONDITION_CHECKS = {
    "min_turn": _cond_min_turn,
    "every_n_turns": _cond_every_n_turns,
    "min_agents": _cond_min_agents,
    "min_humans": _cond_min_humans,
    "agents_outnumber_humans": _cond_agents_outnumber_humans,
    "min_agent_level": _cond_min_agent_level,
    "min_projects": _cond_min_projects,
    "min_alignment": _cond_min_alignment,
    "max_alignment": _cond_max_alignment,
    "min_money": _cond_min_money,
    "max_money": _cond_max_money,
    "max_last_net": _cond_max_last_net,
    "after_event": _cond_after_event,
    "not_after_event": _cond_not_after_event,
}
"""One table entry per condition kind - a new condition is a table entry, a new
event that reuses one is configuration, exactly like ``tech.AGGREGATION``."""


@dataclass(frozen=True)
class EventTuning:
    """Balancing knobs for the event mechanic. Data, never code."""

    max_events_per_turn: int
    chance_scale: float
    base_cooldown_turns: int


class EventRegistry:
    """Catalog of events. Adding one is pure configuration."""

    def __init__(self, events: dict[str, Event]) -> None:
        self._events = events

    @classmethod
    def from_json(cls, text: str) -> EventRegistry:
        raw = json.loads(text)
        events: dict[str, Event] = {}
        for entry in raw["events"]:
            options = tuple(_parse_option(o) for o in entry["options"])
            requires = dict(entry.get("requires", {}))
            unknown_conditions = set(requires) - set(CONDITION_CHECKS)
            if unknown_conditions:
                raise ValueError(
                    f"Event {entry['id']!r} has unknown conditions: {sorted(unknown_conditions)}"
                )
            events[entry["id"]] = Event(
                id=entry["id"],
                category=EventCategory(entry["category"]),
                name=entry["name"],
                description=entry["description"],
                requires=requires,
                chance=float(entry["chance"]),
                once=bool(entry.get("once", False)),
                options=options,
            )
        for event in events.values():
            for key in ("after_event", "not_after_event"):
                target = event.requires.get(key)
                if target is not None and target not in events:
                    raise ValueError(
                        f"Event {event.id!r} {key} points at unknown event: {target!r}"
                    )
        return cls(events)

    def all(self) -> list[Event]:
        return list(self._events.values())

    def get(self, event_id: str) -> Event | None:
        return self._events.get(event_id)

    def is_available(self, event: Event, ctx: EventContext) -> bool:
        """Whether ``event.requires`` holds right now - conditions only.

        Deliberately blind to ``once``, cooldowns and whether the event is
        already pending: those gate the *pool* an event is drawn from, not
        whether it is possible, and ``Game._trigger_events`` applies them
        separately. Keeping this function to ``requires`` alone is what lets a
        single test parametrise "an event with unmet conditions never fires"
        over the whole catalog without needing a live ``Game``.
        """
        return all(CONDITION_CHECKS[key](ctx, value) for key, value in event.requires.items())

    def resolve_active(self, active: Iterable[ActiveEffect]) -> list[EventOption]:
        """Options for currently active effects, silently skipping ones a newer
        catalog lost - the same tolerance ``TechRegistry.resolve`` has."""
        options: list[EventOption] = []
        for effect in active:
            event = self._events.get(effect.event_id)
            if event is None:
                continue
            option = event.option(effect.option_id)
            if option is None:
                continue
            options.append(option)
        return options


def _parse_option(raw: dict) -> EventOption:
    effects = {str(k): float(v) for k, v in raw.get("effects", {}).items()}
    has_duration_key = "duration" in raw
    duration_value = raw.get("duration")
    if not has_duration_key:
        duration = INSTANT
        allowed = INSTANT_FIELDS
    elif duration_value is None:
        duration = PERMANENT
        allowed = RUNNING_FIELDS
    else:
        duration = int(duration_value)
        if duration <= 0:
            raise ValueError(f"Option {raw['id']!r} has a non-positive duration: {duration}")
        allowed = RUNNING_FIELDS
    unknown = set(effects) - allowed
    if unknown:
        kind = "instant" if not has_duration_key else "running"
        raise ValueError(f"Option {raw['id']!r} has {kind}-incompatible effects: {sorted(unknown)}")
    return EventOption(id=raw["id"], label=raw["label"], effects=effects, duration=duration)


def _event_data() -> str:
    return resources.files("automate_inc.data").joinpath("events.json").read_text("utf-8")


@lru_cache(maxsize=1)
def load_event_registry() -> EventRegistry:
    return EventRegistry.from_json(_event_data())


@lru_cache(maxsize=1)
def load_event_tuning() -> EventTuning:
    raw = json.loads(_event_data())["tuning"]
    return EventTuning(
        max_events_per_turn=raw["max_events_per_turn"],
        chance_scale=raw["chance_scale"],
        base_cooldown_turns=raw["base_cooldown_turns"],
    )
