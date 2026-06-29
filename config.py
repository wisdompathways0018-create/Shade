from database import get_guild, save


def get_server(server_id):
    return get_guild(server_id)


def save_server():
    save()