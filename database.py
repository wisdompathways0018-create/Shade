import json
import os
import time

DATABASE_FILE = "database.json"
GIVEAWAY_RETENTION_SECONDS = 7 * 24 * 60 * 60


def load_database():
    if not os.path.exists(DATABASE_FILE):
        return {}
    try:
        with open(DATABASE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _cleanup_expired_data(data):
    """Remove only explicitly disposable records, independently per guild."""
    now = time.time()
    for guild_data in data.values():
        if not isinstance(guild_data, dict):
            continue
        giveaways = guild_data.get("giveaways")
        if isinstance(giveaways, dict):
            for giveaway_id in list(giveaways):
                giveaway = giveaways.get(giveaway_id)
                if not isinstance(giveaway, dict):
                    continue
                ends_at = giveaway.get("ends_at")
                if isinstance(ends_at, (int, float)) and giveaway.get("ended") and now - ends_at >= GIVEAWAY_RETENTION_SECONDS:
                    del giveaways[giveaway_id]


def save_database(data):
    _cleanup_expired_data(data)
    temporary_file = f"{DATABASE_FILE}.tmp"
    with open(temporary_file, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    os.replace(temporary_file, DATABASE_FILE)


database = load_database()


def get_guild(guild_id):
    guild_id = str(guild_id)
    if guild_id not in database:
        database[guild_id] = {
            "alliance_name": None,
            "timezone": "UTC",
            "ping_role": None,
            "frost": [], "ib": [], "ke": [], "supremacy": [], "cor": [], "lords": [], "relic": [], "malena": [], "custom_events": [],
            "frost_channel": None, "ib_channel": None, "ke_channel": None, "as_channel": None, "cor_channel": None, "malena_channel": None,
            "warning_channel": None, "welcome_channel": None, "leave_channel": None,
            "moderation_warnings": {}, "moderation_warning_tickets": []
        }
        save_database(database)
    else:
        guild = database[guild_id]
        guild.setdefault("moderation_warnings", {})
        guild.setdefault("moderation_warning_tickets", [])
        guild.setdefault("warning_channel", None)
        guild.setdefault("welcome_channel", None)
        guild.setdefault("leave_channel", None)
    return database[guild_id]


def save():
    save_database(database)
