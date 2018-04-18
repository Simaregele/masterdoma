import asyncio
from aiohttp import web
# сервер еба )
routes = web.RouteTableDef()

@routes.post('/site_script')
async def main(request):
    data = await request.post()
    print(data)
    return web.Response(text='test')

print('WOW')
app = web.Application()
app.add_routes(routes)
web.run_app(app, port=30003)
