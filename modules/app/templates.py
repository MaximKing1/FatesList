from ..deps import *

router = APIRouter(
    prefix = "/template",
    tags = ["Templates"],
    include_in_schema = False
)

@router.get("/")
async def tmpl_rdir(request: Request):
    return RedirectResponse("/")

@router.get("/{name}")
async def tmpl_index(request: Request, bot_id: int):
    return await render_bot(request, bot_id, review = False, widget = False)

@router.get("/{name}/description")
async def tmpl_desc(request: Request, bot_id: int):
    bot = await db.fetchrow("SELECT long_description FROM bots WHERE bot_id = $1",int(bot_id))
    if bot:
        return templates.TemplateResponse("description.html",{"request":request,"bot":bot})
    else:
        return "Bot not found! :( Try refreshing. After that either report it on the support server or just continue your day!"

@router.get("/{bot_id}/widget")
async def tmpl_widget(request: Request, bot_id: int):
    return await render_bot(request, bot_id, review = False, widget = True)