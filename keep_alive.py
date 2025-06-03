from aiohttp import web

async def handle(request):
    return web.Response(text="Bot is alive!")

def keep_alive():
    app = web.Application()
    app.router.add_get("/", handle)
    web.run_app(app, port=8080)
