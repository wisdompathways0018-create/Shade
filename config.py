# ==========================================
# Shade Configuration
# ==========================================

server_config = {}


def create_server(server_id):
    if server_id not in server_config:
        server_config[server_id] = {
            "alliance_name": None,
            "timezone": "UTC",
            "reminder_channel": None,
            "ping_role": "@everyone",

            "frost": [],
            "supremacy": {},
            "relic": {},
            "lords": {},
            "malena": {},
            "custom_events": []
        }


def get_server(server_id):
    create_server(server_id)
    return server_config[server_id]