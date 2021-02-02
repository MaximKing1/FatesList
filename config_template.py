# Copy this to config.py when deploying
import builtins
builtins.bot_logs=798954080604520509
builtins.reviewing_server=794834630942654546 # Bit of a misnomer, but this is the actual main server
builtins.test_server = 794834630942654546 # And THIS is the test server for reviewing bots
# Confusing right? Sorry, i already did 50% using reviewing server so meow ig
builtins.staff_roles = {
    "guild": {
        "id": 00000000000000000,
        "perm": 1
    },
    "bot_review": {
        "id": 798954440132526120,
        "perm": 2
    },
    "mod": {
        "id": 798954778042433576,
        "perm": 3
    },
    "admin": {
        "id": 798954635234508820,
        "perm": 4,
    },
    "owner": {
        "id": 798956804511629312,
        "perm": 5,
    }
}
builtins.site = "dev.fateslist.xyz" # Replace this with your main site

# This value below dont need to be changed
builtins.site_url = "https://" + site

builtins.support_url = "https://discord.gg/PA5vjCRc5H"
builtins.TOKEN = "TOKEN HERE"
builtins.TAGS = {"music": "fa-music", "moderation": "fa-hammer", "economy": "", "fun": "", "anime": "", "games": "", "web_dashboard": "", "logging": "", "streams": "", "game_stats": "", "leveling": "", "roleplay": "", "utility": "", "social": ""}
builtins.pg_user = "postgres" # Postgres Database Username
builtins.pg_pwd = "" # Postgres Database Password
builtins.pg_db = "fateslist-dev"
builtins.csrf_secret = ""
builtins.session_key = ""
class OauthConfig:
    client_id = "CLIENT ID HERE"
    client_secret = "CLIENT SECRET HERE"
    scope = ["identify"]
    redirect_uri = "https://" + site + "/auth/login/confirm"

