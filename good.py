"""Find devices on the network, and pick one to start streaming snapclient to

python test.py
"""

import asyncio
import asyncio.subprocess as asp
import sys


from typing import List
import pyatv
from pyatv.interface import Playing, PushListener
from pyatv.const import Protocol
from pyatv.conf import BaseConfig

chunk_size = 1024
LOOP = asyncio.get_event_loop()

# Create my own wrapper for the audio buffer?
    

async def create_process(cmd, *args):
    process = await asp.create_subprocess_exec(
        cmd, stdin=None, stdout=asp.PIPE, stderr=None, *args)
    return process

def handle_device(device: BaseConfig):
    print(f"Found device: {device.name} {device.device_info.model}, address: {device.address}")

def get_valid_devices(devices: List[BaseConfig]):
    return devices



class PushUpdatePrinter(PushListener):
    """Print push updates to console."""

    def playstatus_update(self, updater, playstatus: Playing) -> None:
        """Inform about changes to what is currently playing."""
        print(30 * "-" + "\n", playstatus)

    def playstatus_error(self, updater, exception: Exception) -> None:
        """Inform about an error when updating play status."""
        print("Error:", exception)


async def pair(conf: BaseConfig, loop: asyncio.AbstractEventLoop):
    pairing = await pyatv.pair(conf, Protocol.RAOP, loop)
    await pairing.begin()

    pin = int(input("Enter PIN: "))
    pairing.pin(pin)
    await pairing.finish()

    # Give some feedback about the process
    if pairing.has_paired:
        print("Paired with device!")
        print("Credentials:", pairing.service.credentials)
    else:
        print("Did not pair with device!")

    await pairing.close()

async def stream_with_push_updates(
    conf: BaseConfig, loop: asyncio.AbstractEventLoop
):
    """Find a device and print what is playing."""
    print("* Connecting to", conf.address)
    
    # await pair(conf, loop)
    atv = await pyatv.connect(conf, loop)

    listener = PushUpdatePrinter()
    atv.push_updater.listener = listener
    atv.push_updater.start()

    process = await create_process("./snapclient.sh")
    try:
        print("* Starting to stream")
        await atv.stream.stream_file(process.stdout)
        await asyncio.sleep(0.01)
    except Exception as e:
        print(e)
    finally:
        atv.close()

async def scan(
    loop: asyncio.AbstractEventLoop
):
    """Find a device and print what is playing."""
    print("* Discovering devices on network...")
    atvs = await pyatv.scan(loop, protocol=Protocol.RAOP)

    if not atvs:
        print("* Device found", file=sys.stderr)
        return
    devices = get_valid_devices(atvs)

    if not devices:
        print("* No Valid Devices found", file=sys.stderr)
        return
    await select_to_stream(devices, loop)
    return devices
async def select_to_stream(
    devices: List[BaseConfig],
    loop: asyncio.AbstractEventLoop
):
    """Find a device and print what is playing."""
    for i, device in enumerate(devices, start=1):
        print(f"{i}: {device.name} {device.device_info.model}, address: {device.address}")
    selection = -1
    while selection < 0:
        user_input = input("Pick a device by number: ")
        try:
            converted = int(user_input) - 1
            if len(devices) > converted:
                selection = converted
        except:
            print(f"{user_input} was not a valid device choice")
    
    device = devices[selection]

    await stream_with_push_updates(device, loop)



if __name__ == "__main__":
    LOOP.run_until_complete(scan(LOOP))