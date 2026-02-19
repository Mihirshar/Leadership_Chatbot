import yaml
from pathlib import Path
from typing import Optional


def load_leader_config(yaml_path: Path) -> dict:
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_all_leaders(config_dir: Optional[str] = None) -> dict:
    if config_dir is None:
        config_dir = Path("config/leaders")
    else:
        config_dir = Path(config_dir)

    leaders = {}
    if not config_dir.exists():
        return leaders

    for yaml_file in sorted(config_dir.glob("*.yaml")):
        data = load_leader_config(yaml_file)
        leaders[data["id"]] = data

    return leaders


def get_leader_summary(leader: dict) -> str:
    p = leader["personality"]
    return (
        f"{leader['name']} — {leader['role']}\n"
        f"Style: {p['communication_style']}\n"
        f"Philosophy: {p['leadership_philosophy']}"
    )


BADGES = {
    "first_question": {
        "name": "Ice Breaker",
        "icon": "🧊",
        "description": "Asked your first question",
        "threshold": 1,
    },
    "curious_mind": {
        "name": "Curious Mind",
        "icon": "🔍",
        "description": "Asked 5 questions",
        "threshold": 5,
    },
    "deep_thinker": {
        "name": "Deep Thinker",
        "icon": "🧠",
        "description": "Asked 10 questions",
        "threshold": 10,
    },
    "leadership_explorer": {
        "name": "Leadership Explorer",
        "icon": "🧭",
        "description": "Chatted with 2 different leaders",
        "threshold": 2,
    },
    "summit_champion": {
        "name": "Summit Champion",
        "icon": "🏆",
        "description": "Chatted with all leaders",
        "threshold": 3,
    },
}


def check_badges(questions_asked: int, leaders_chatted: int, total_leaders: int) -> list:
    earned = []
    if questions_asked >= BADGES["first_question"]["threshold"]:
        earned.append(BADGES["first_question"])
    if questions_asked >= BADGES["curious_mind"]["threshold"]:
        earned.append(BADGES["curious_mind"])
    if questions_asked >= BADGES["deep_thinker"]["threshold"]:
        earned.append(BADGES["deep_thinker"])
    if leaders_chatted >= BADGES["leadership_explorer"]["threshold"]:
        earned.append(BADGES["leadership_explorer"])
    if leaders_chatted >= total_leaders and total_leaders > 0:
        earned.append(BADGES["summit_champion"])
    return earned


def get_xp_level(xp: int) -> tuple[int, str, int]:
    """Returns (level, title, xp_for_next_level)."""
    levels = [
        (0, "Observer"),
        (100, "Apprentice"),
        (300, "Strategist"),
        (600, "Advisor"),
        (1000, "Visionary"),
        (1500, "Oracle"),
    ]
    current_level = 0
    current_title = levels[0][1]
    next_threshold = levels[1][0] if len(levels) > 1 else 9999

    for i, (threshold, title) in enumerate(levels):
        if xp >= threshold:
            current_level = i
            current_title = title
            next_threshold = levels[i + 1][0] if i + 1 < len(levels) else threshold + 500

    return current_level, current_title, next_threshold
