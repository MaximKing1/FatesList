from ..deps import *

router = APIRouter(
    prefix = "/admin",
    tags = ["Admin"],
    include_in_schema = False
)

@router.get("/console")
async def admin_dashboard(request:Request, stats: Optional[int] = 0):
    if "userid" in request.session.keys() or stats == 1:
        if "userid" in request.session.keys() and stats != 1:
            guild = client.get_guild(reviewing_server)
            user = guild.get_member(int(request.session["userid"]))
            if user is None:
                return RedirectResponse("/", status_code = 303)
            staff = is_staff(staff_roles, user.roles, 2)
            if not staff[0]:
                return RedirectResponse("/", status_code = 303)
        certified_bots = len(await db.fetch("SELECT bot_id FROM bots WHERE certified = true"))
        bots = len(await db.fetch("SELECT bot_id FROM bots WHERE queue = false"))
        fetch = await db.fetch("SELECT bot_id, votes, servers, description, banned FROM bots WHERE queue = true")
        banned = await db.fetch("SELECT bot_id FROM bots WHERE banned = true")
        queue_bots = []
        queue_amount = len([i for i in fetch if not i["banned"]])
        form = await Form.from_formdata(request)
        # TOP VOTED BOTS
        for bot in fetch:
            bot_info = await get_bot(bot["bot_id"])
            if bot_info is None:
                continue
            bot_info = {"username": bot_info["username"], "id": bot["bot_id"], "avatar": bot_info["avatar"], "form": form, "banned": bot["banned"]}
            if bot_info:
                queue_bots.append({"bot": bot, "id": bot["bot_id"], "avatar": bot_info["avatar"], "username": bot_info["username"], "votes": human_format(bot["votes"]), "servers": human_format(bot["servers"]), "description": bot["description"], "form": form, "banned": bot_info["banned"]})
        return templates.TemplateResponse("admin_stats.html",{"request": request, "cert": certified_bots,"bots": bots, "queue_bots": queue_bots, "queue_amount": queue_amount, "admin": stats != 1 and staff[1] == 4, "mod": stats != 1 and staff[1] == 3, "owner": stats != 1 and staff[1] == 5, "bot_review": stats != 1 and staff[1] == 2, "form": form, "banned": banned, "stats": stats == 1})
    else:
        return RedirectResponse("/", status_code = 303)

@router.post("/console")
@csrf_protect
async def admin_api(request:Request, admin: str = FForm(""), bot_id: int = FForm(0), bt: BackgroundTasks):
    print(bot_id)
    guild = client.get_guild(reviewing_server)
    user = guild.get_member(int(request.session["userid"]))
    if user is None:
        return RedirectResponse("/")
    if not is_staff(staff_roles, user.roles, 5)[0]:
        return RedirectResponse("/admin/console", status_code = 303) 
    if admin=="certify":
        users = await db.fetchrow("SELECT owner, extra_owners FROM bots WHERE bot_id = $1", bot_id)
        if users is None:
            return RedirectResponse("/admin/console", status_code = 303)
        await db.execute("UPDATE bots SET certified = true WHERE bot_id = $1", bot_id)
        await db.execute("UPDATE users SET certified = true WHERE userid = $1", int(users["owner"]))
        if users["extra_owners"] is None:
            eo = []
        else:
            eo = users["extra_owners"]
        for user in eo:
            await db.execute("UPDATE users SET certified = true WHERE userid = $1", int(user))
        channel = client.get_channel(bot_logs)
        owner=str(request.session["userid"])
        await channel.send(f"<@{owner}> certified the bot <@{bot_id}>")
        return templates.TemplateResponse("message.html", {"request": request, "message": "Hey mikes, i hope it certified the bot!", "username": request.session.get("username", False)})
    elif admin=="uncertify":
        await db.execute("UPDATE bots SET certified = false WHERE bot_id = $1", bot_id)
        channel = client.get_channel(bot_logs)
        owner=str(request.session["userid"])
        await channel.send(f"<@{owner}> uncertified the bot <@{bot_id}>")
        return templates.TemplateResponse("message.html", {"request": request, "message": "Hey mikes, i hope it uncertified the bot!", "username": request.session.get("username", False)})
    elif admin == "whitelist":
        await db.execute("UPDATE bots SET autovote_whitelist = true WHERE bot_id = $1", bot_id)
        return "Done"
    elif admin == "unwhitelist":
        await db.execute("UPDATE bots SET autovote_whitelist = false WHERE bot_id = $1", bot_id)
        return "Done"
    elif admin=="reset":
        bt.add_task(stat_update_bt)        
        return templates.TemplateResponse("message.html", {"request": request, "message": "Hey mikes, i hope your wish comes true ;)", "username": request.session.get("username", False)})
    else:
        return RedirectResponse("/admin/console", status_code = 303)

async def stat_update_bt():
    bots = await db.fetch("SELECT bot_id, votes FROM bots")
    for bot in bots:
        await db.execute("INSERT INTO bot_stats_votes_pm (bot_id, epoch, votes) VALUES ($1, $2, $2)", bot["bot_id"], time.time(), bot["votes"])
    await db.execute("UPDATE bots SET votes = 0")

@router.get("/review/{bot_id}")
async def review(request: Request, bot_id: int):
    if "userid" in request.session.keys():
        guild = client.get_guild(reviewing_server)
        user = guild.get_member(int(request.session["userid"]))
        s = is_staff(staff_roles, user.roles, 2)
        if not s[0]:
            return RedirectResponse("/")
        # async def _get_bot(bot_id: int, review: bool):
        return await render_bot(request, bot_id, review = True, widget = False)
    else:
        return RedirectResponse("/") 

@router.post("/review/{bot_id}")
async def review_api(request:Request, bot_id: int, accept: str = FForm("")):
    guild = client.get_guild(reviewing_server)
    user = guild.get_member(int(request.session["userid"]))
    s = is_staff(staff_roles, user.roles, 2)
    if not s[0]:
        return RedirectResponse("/")                
    elif accept == "true":
        b = await db.fetchrow("SELECT owner, extra_owners FROM bots WHERE bot_id = $1", bot_id)
        if b is None:
            return RedirectResponse("/admin/console")
        await db.execute("UPDATE bots SET queue=false WHERE bot_id = $1", bot_id)
        await add_event(bot_id, "approve", {"user": request.session.get('userid')})
        channel = client.get_channel(bot_logs)
        await channel.send(f"<@{bot_id}> by <@{str(b['owner'])}> has been approved")
        
        # Give Bot Dev Roles
        try:
            owner = guild.get_member(int(b['owner']))
        except:
            owner = None
        if owner is None:
            pass
        else:
            await owner.add_roles(guild.get_role(bot_dev_role))
        if b["extra_owners"] is None:
            pass
        else:
            for eo in b["extra_owners"]:
                try:
                    eo_member = guild.get_member(int(eo))
                except:
                    eo_member = None
                if eo_member is None:
                    pass
                else:
                    await eo_member.add_roles(guild.get_role(bot_dev_role))

        return templates.TemplateResponse("last.html",{"request":request,"message":"Bot accepted; You MUST Invite it by this url","username":request.session["username"],"url":f"https://discord.com/oauth2/authorize?client_id={str(bot_id)}&scope=bot&guild_id={guild.id}&disable_guild_select=true&permissions=0"})
    elif accept == "unverify":
        b = await db.fetchrow("SELECT owner FROM bots WHERE bot_id = $1", bot_id)
        if b is None:
            return RedirectResponse("/admin/console")
        await db.execute("UPDATE bots SET queue=true, banned = false WHERE bot_id = $1", bot_id)
        await add_event(bot_id, "unverify", {"user": request.session.get('userid')})
        channel = client.get_channel(bot_logs)
        await channel.send(f"<@{bot_id}> by <@{str(b['owner'])}> has been unverified")
        return templates.TemplateResponse("message.html",{"request":request,"message":"Bot unverified. Please carry on with your day"})
    elif accept == "false":
        return RedirectResponse("/admin/review/"+str(bot_id)+"/deny", status_code=303)
    else:
        return RedirectResponse("/")

@router.get("/review/{bot_id}/deny")
async def review_deny(request:Request, bot_id: int):
    if "userid" in request.session.keys():
        form = await Form.from_formdata(request)
        guild = client.get_guild(reviewing_server)
        user = guild.get_member(int(request.session["userid"]))
        s = is_staff(staff_roles, user.roles, 2)
        if not s[0]:
            return RedirectResponse("/")            
        else:    
            bot = await db.fetchrow("SELECT * FROM bots WHERE bot_id = $1 AND queue = true",int(bot_id))
            if not bot:
                return templates.TemplateResponse("message.html",{"request":request,"message":"Bot does not exist! Idk how"})
            return templates.TemplateResponse("last_deny.html",{"request":request,"bot":bot,"username":request.session["username"], "form": form})

@router.post("/review/{bot_id}/deny")
async def review_deny_api(request:Request, bot_id: int, reason: str = FForm("There was no reason specified")):
    guild = client.get_guild(reviewing_server)
    user = guild.get_member(int(request.session["userid"]))
    s = is_staff(staff_roles, user.roles, 2)
    if not s[0]:
        return RedirectResponse("/")
    else:
        check = await db.fetchrow("SELECT owner FROM bots WHERE bot_id=$1 and queue=true", bot_id)
        if not check:
            return templates.TemplateResponse("message.html",{"request":request,"message":"Bot does not exist! Idk how"})
        await db.execute("UPDATE bots SET banned = true WHERE bot_id = $1", bot_id)
        owner=str(request.session["userid"])
        await add_event(bot_id, "deny", {"user": request.session.get('userid')})
        channel = client.get_channel(bot_logs)
        await channel.send(f"<@{owner}> has denied the bot <@{bot_id}> by <@{str(check['owner'])}> with the reason: {reason}")
        return templates.TemplateResponse("message.html",{"request":request,"message":"I hope it DENIED the bot review GUY","username":request.session["username"]})
