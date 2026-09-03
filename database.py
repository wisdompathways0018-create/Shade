import json
import os

DATABASE_FILE = "database.json"


def load_database():

    if not os.path.exists(DATABASE_FILE):
        return {}

    try:

        with open(DATABASE_FILE, "r") as f:
            return json.load(f)

    except Exception:
        return {}


def save_database(data):

    with open(DATABASE_FILE, "w") as f:
        json.dump(data, f, indent=4)


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
