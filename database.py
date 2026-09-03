import json
import os
import time

DATABASE_FILE = "database.json"

# Only data explicitly listed here is considered disposable. Persistent
# server data such as birthdays, levels, suggestions, events and settings is
# never removed automatically.
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
    changed = False

    for guild_data in data.values():
        if not isinstance(guild_data, dict):
            continue

        giveaways = guild_data.get("giveaways")
        if isinstance(giveaways, dict):
            expired_ids = []
            for giveaway_id, giveaway in giveaways.items():
                if not isinstance(giveaway, dict):
                    continue
                ends_at = giveaway.get("ends_at")
                if not isinstance(ends_at, (int, float)):
                    continue
                if giveaway.get("ended") and now - ends_at >= GIVEAWAY_RETENTION_SECONDS:
                    expired_ids.append(giveaway_id)

            for giveaway_id in expired_ids:
                del giveaways[giveaway_id]
                changed = True

    return changed


def save_database(data):
    # Cleanup is deliberately allow-list based: unknown/persistent keys are
    # untouched so one server's birthday, event, level, suggestion, etc. can
    # never be deleted by the storage cleanup.
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

            "frost": [],
            "ib": [],
            "ke": [],
            "supremacy": [],
            "cor": [],
            "lords": [],
            "relic": [],
            "malena": [],
            "custom_events": [],

            "frost_channel": None,
            "ib_channel": None,
            "ke_channel": None,
            "as_channel": None,
            "cor_channel": None,
            "malena_channel": None,
            "warning_channel": None,

            "moderation_warnings": {},
            "moderation_warning_tickets": []
        }

        save_database(database)

    else:
        # Backward-compatible migration for existing guild records.
        database[guild_id].setdefault("moderation_warnings", {})
        database[guild_id].setdefault("moderation_warning_tickets", [])
        database[guild_id].setdefault("warning_channel", None)

    return database[guild_id]


def save():

    save_database(database)
