from fastapi import FastAPI, Request, Form as FForm
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.templating import Jinja2Templates
import asyncpg
from pydantic import BaseModel
import discord
import asyncio
from starlette_wtf import CSRFProtectMiddleware
import builtins
import importlib
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from modules.deps import *
from config import *
import orjson
import os
import aioredis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import logging
from fastapi.exceptions import HTTPException 
#logging.basicConfig(level=logging.DEBUG)

# SlowAPI rl func
async def rl_key_func(request: Request) -> str:
    if request.headers.get("FatesList-RateLimitBypass") == ratelimit_bypass_key:
        return get_token(32)
    if "Authorization" in request.headers or "authorization" in request.headers:
        try:
            r = request.headers["Authorization"]
        except KeyError:
            r = request.headers["authorization"]
        check = await db.fetchrow("SELECT bot_id, certified FROM bots WHERE api_token = $1", r)
        if check is None:
            return ip_check(request)
        if check["certified"]:
            return get_token(32)
        return r
    else:
        return ip_check(request)

def ip_check(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host

# Setup Bots

intent_main = discord.Intents.default()
intent_main.typing = False
intent_main.bans = False
intent_main.emojis = False
intent_main.integrations = False
intent_main.webhooks = False
intent_main.invites = False
intent_main.voice_states = False
intent_main.messages = False
intent_main.members = True
intent_main.presences = True
builtins.client = discord.Client(intents=intent_main)

intent_server = discord.Intents.default()
intent_server.typing = False
intent_server.bans = False
intent_server.emojis = False
intent_server.integrations = False
intent_server.webhooks = False
intent_server.invites = True
intent_server.voice_states = False
intent_server.messages = False
intent_server.members = True
intent_server.presences = False
builtins.client_servers = discord.Client(intents=intent_server)

limiter = FastAPILimiter
app = FastAPI(default_response_class = ORJSONResponse, docs_url = None, redoc_url = "/api/docs/endpoints")
app.add_middleware(SessionMiddleware, secret_key=session_key)

app.add_middleware(CSRFProtectMiddleware, csrf_secret=csrf_secret)
app.add_middleware(ProxyHeadersMiddleware)

@app.exception_handler(401)
@app.exception_handler(404)
@app.exception_handler(RequestValidationError)
@app.exception_handler(ValidationError)
@app.exception_handler(500)
@app.exception_handler(HTTPException)
@app.exception_handler(Exception)
async def validation_exception_handler(request, exc):
    return await FLError.error_handler(request, exc)

print("FATES LIST: Loading Modules")
# Include all the modules
for f in os.listdir("modules/app"):
    if not f.startswith("_"):
        print("APP MODLOAD: modules.app." + f.replace(".py", ""))
        route = importlib.import_module("modules.app." + f.replace(".py", ""))
        app.include_router(route.router)

async def setup_db():
    db = await asyncpg.create_pool(host="127.0.0.1", port=5432, user=pg_user, password=pg_pwd, database="fateslist")
    # some table creation here meow
    return db

@app.on_event("startup")
async def startup():
    builtins.db = await setup_db()
    print("Discord init beginning")
    asyncio.create_task(client.start(TOKEN_MAIN))
    asyncio.create_task(client_servers.start(TOKEN_SERVER))
    await asyncio.sleep(4)
    builtins.redis_db = await aioredis.create_redis_pool('redis://localhost')
    limiter.init(redis_db, identifier = rl_key_func)

@app.on_event("shutdown")
async def close():
    print("Closing")
    redis_db.close()
    await redis_db.wait_closed()

@client.event
async def on_ready():
    print(client.user, "up")

@client_servers.event
async def on_ready():
    print(client_servers.user, "up [SERVER BOT]")


# Tag calculation
builtins.tags_fixed = []
for tag in TAGS.keys():
    tags_fixed.append({"name": tag.replace("_", " ").title(), "iconify_data": TAGS[tag], "id": tag})

builtins.server_tags_fixed = []
for tag in SERVER_TAGS.keys():
    server_tags_fixed.append({"name": tag.replace("_", " ").title(), "iconify_data": SERVER_TAGS[tag], "id": tag})

