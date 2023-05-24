import asyncio
import asyncio.subprocess as asp
from aiohttp import WSMsgType, web
from pyatv.const import Protocol
import pyatv
import json
import os
import pathlib

file_path = pathlib.Path(os.path.realpath(__file__)).parent
PAGE = """
<script>
let socket = new WebSocket('ws://' + location.host + '/ws/DEVICE_ID');

socket.onopen = function(e) {
  document.getElementById('status').innerText = 'Connected!';
};

socket.onmessage = function(event) {
  document.getElementById('state').innerText = event.data;
};

socket.onclose = function(event) {
  if (event.wasClean) {
    document.getElementById('status').innerText = 'Connection closed cleanly!';
  } else {
    document.getElementById('status').innerText = 'Disconnected due to error!';
  }
  document.getElementById('state').innerText = "";
};

socket.onerror = function(error) {
  document.getElementById('status').innerText = 'Failed to connect!';
};
</script>
<div id="status">Connecting...</div>
<div id="state"></div>
"""

routes = web.RouteTableDef()

async def create_process(cmd, *args):
    process = await asp.create_subprocess_exec(
        cmd, stdin=None, stdout=asp.PIPE, stderr=None, *args)
    return process


class DeviceListener(pyatv.interface.DeviceListener, pyatv.interface.PushListener):
    def __init__(self, app, identifier):
        self.app = app
        self.identifier = identifier

    def connection_lost(self, exception: Exception) -> None:
        self._remove()

    def connection_closed(self) -> None:
        self._remove()

    def _remove(self):
        self.app["atv"].pop(self.identifier)
        self.app["listeners"].remove(self)

    def playstatus_update(self, updater, playstatus: pyatv.interface.Playing) -> None:
        clients = self.app["clients"].get(self.identifier, [])
        for client in clients:
            asyncio.ensure_future(client.send_str(str(playstatus)))

    def playstatus_error(self, updater, exception: Exception) -> None:
        pass


def web_command(method):
    async def _handler(request):
        device_id = request.match_info["id"]
        atv = request.app["atv"].get(device_id)
        if not atv:
            return web.Response(text=f"Not connected to {device_id}", status=500)
        return await method(request, atv)

    return _handler


def add_credentials(config, query):
    for service in config.services:
        proto_name = service.protocol.name.lower()
        if proto_name in query:
            config.set_credentials(service.protocol, query[proto_name])


@routes.get("/state/{id}")
async def state(request):
    return web.Response(
        text=PAGE.replace("DEVICE_ID", request.match_info["id"]),
        content_type="text/html",
    )


@routes.get("/scan")
async def scan(request):
    results = await pyatv.scan(loop=asyncio.get_event_loop())
    if results:
        output = "\n\n".join(str(result) for result in results)
    else:
        output = "No devices found"
    return web.Response(text=output)


@routes.get("/connect/{id}")
async def connect(request):
    loop = asyncio.get_event_loop()
    device_id = request.match_info["id"]
    if device_id in request.app["atv"]:
        return web.Response(text=f"Already connected to {device_id}")

    results = await pyatv.scan(identifier=device_id, loop=loop)
    if not results:
        return web.Response(text="Device not found", status=500)

    add_credentials(results[0], request.query)

    try:
        atv = await pyatv.connect(results[0], loop=loop)
    except Exception as ex:
        return web.Response(text=f"Failed to connect to device: {ex}", status=500)

    
    process = await create_process(f'python', f'{file_path}/main.py', f'{device_id}')
    request.app["processes"][device_id] = process
    listener = DeviceListener(request.app, device_id)
    atv.listener = listener
    atv.push_updater.listener = listener
    atv.push_updater.start()
    request.app["listeners"].append(listener)

    request.app["atv"][device_id] = atv
    save_processes_to_settings(request.app)
    return web.Response(text=f"Connected to device {device_id}")

async def connect_and_create(app: web.Application, device_id: str, query: any = None) -> bool:
    loop = asyncio.get_event_loop()
    if device_id in app["atv"]:
        return False

    results = await pyatv.scan(identifier=device_id, loop=loop)
    if not results:
        return False

    if query is None:
        query = {}
    add_credentials(results[0], query)

    try:
        atv = await pyatv.connect(results[0], loop=loop)
    except Exception as ex:
        return False

    process = await create_process(f'python', f'{file_path}/main.py', f'{device_id}')
    app["processes"][device_id] = process
    listener = DeviceListener(app, device_id)
    atv.listener = listener
    atv.push_updater.listener = listener
    atv.push_updater.start()
    app["listeners"].append(listener)

    app["atv"][device_id] = atv
    save_processes_to_settings(app)
    return True


@routes.get("/remote_control/{id}/{command}")
@web_command
async def remote_control(request, atv):
    try:
        await getattr(atv.remote_control, request.match_info["command"])()
    except Exception as ex:
        return web.Response(text=f"Remote control command failed: {ex}")
    return web.Response(text="OK")


@routes.get("/playing/{id}")
@web_command
async def playing(request, atv):
    try:
        status = await atv.metadata.playing()
    except Exception as ex:
        return web.Response(text=f"Remote control command failed: {ex}")
    return web.Response(text=str(status))


@routes.get("/volume/{id}/{level}")
@web_command
async def set_volume(request, atv):
    loop = asyncio.get_event_loop()
    device_id = request.match_info["id"]
    volume = request.match_info["level"]
    if device_id in request.app["atv"]:
        device = request.app["atv"][device_id]
        asyncio.ensure_future(device.audio.set_volume(float(volume)))
        return web.Response(text=f"Already connected to {device_id}")

    return web.Response(text=f"Volume command failed", status=500)

@routes.get("/close/{id}")
@web_command
async def close_connection(request, atv):
    device_id = request.match_info["id"]
    try:
        process = request.app["processes"][device_id]
        process.terminate()
    except Exception as ex:
        return web.Response(text=f"Close command failed: {ex}")
    atv.close()
    return web.Response(text="OK")


@routes.get("/ws/{id}")
@web_command
async def websocket_handler(request, pyatv):
    device_id = request.match_info["id"]

    ws = web.WebSocketResponse()
    await ws.prepare(request)
    request.app["clients"].setdefault(device_id, []).append(ws)

    playstatus = await pyatv.metadata.playing()
    await ws.send_str(str(playstatus))

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            # Handle custom commands from client here
            if msg.data == "close":
                await ws.close()
        elif msg.type == WSMsgType.ERROR:
            print(f"Connection closed with exception: {ws.exception()}")

    request.app["clients"][device_id].remove(ws)

    return ws

def save_processes_to_settings(app: web.Application) -> bool:
    try:
        running = list(app.get("processes", {}).keys())
        data = {'ids': running}
        print(f"Dumping {data}")
        with open('settings.json', 'w') as f:
            json.dump(data, f)
        return True
    except:
        return False

def load_device_ids() -> list:
    try:
        with open('settings.json', 'r') as f:
            data = json.load(f)
            print(f"Got settings {data}")
            return data.get('ids', [])
    except:
        print("Failed to load existing ids")
        return []

async def on_startup(app: web.Application) -> None:
    device_ids = load_device_ids()
    for device_id in device_ids:
        print(f"Connecting to {device_id}")
        await connect_and_create(app, device_id)
        

async def on_shutdown(app: web.Application) -> None:
    save_processes_to_settings(app)
    for device_id in app.get("processes", {}).keys():
        p = app['processes'][device_id]
        try:
            print("killing", p)
            p.terminate()
        except Exception as e:
            print(f"Couldn't kill the process for {device_id}", e)
        
    for atv in app["atv"].values():
        atv.close()


def main():
    app = web.Application()
    print("loading app")
    app["atv"] = {}
    app["listeners"] = []
    app["processes"] = {}
    app["clients"] = {}
    print('adding routes')
    app.add_routes(routes)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, host='0.0.0.0', port=8080)


if __name__ == "__main__":
    print("starting")
    main()