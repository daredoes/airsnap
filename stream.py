import asyncio
from aiohttp import web

async def create_process(cmd, *args):
    process = await asyncio.subprocess.create_subprocess_exec(
        cmd, stdin=None, stdout=asyncio.subprocess.PIPE, stderr=None, *args)
    return process

async def stream_pcm(request):
    resp = web.StreamResponse()
    resp.content_type = 'audio/mpeg'  # You might need to adjust the content type depending on your specific needs

    await resp.prepare(request)
    process = await create_process("./snapclient.sh")

    while True:
        data = await process.stdout.read(4096)
        if not data:
            break
        try:
          await resp.write(data)
        except ConnectionResetError:
            process.kill()

    return resp

app = web.Application()
app.router.add_get('/stream', stream_pcm)

web.run_app(app)
