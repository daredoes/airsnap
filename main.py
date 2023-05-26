"""Find devices on the network, and pick one to start streaming snapclient to

python test.py
"""

import asyncio
import asyncio.subprocess as asp
import sys
import json

from typing import List
import pyatv
from pyatv.interface import Playing, PushListener
from pyatv.const import Protocol, PairingRequirement
from pyatv.conf import BaseConfig

chunk_size = 1024
LOOP = asyncio.get_event_loop()

# Create my own wrapper for the audio buffer?
    

async def create_process(cmd, *args, **kwargs):
    process = await asp.create_subprocess_exec(
        cmd, stdin=None, stdout=asp.PIPE, stderr=None, env=kwargs.get('env'), *args)
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
    credentials = load_credentials()
    saved_credentials = credentials[conf.identifier]
    if saved_credentials:
        # Find device and restore credentials
        atvs = pyatv.scan(loop, identifier=conf.identifier, protocol=Protocol.RAOP)
        atv = atvs[0]
        atv.set_credentials(Protocol.RAOP, saved_credentials)
        return True
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

def load_credentials():
    data = {}
    with open('credentials.json', 'r') as f:
        data = json.load(f)
    return data

def save_credentials(identifier: str, credentials: str):
    data = load_credentials()
    data[identifier] = credentials
    with open('credentials.json', 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)
    return True

async def stream_with_push_updates(
    conf: BaseConfig, loop: asyncio.AbstractEventLoop, instance: int = 1,
):
    """Find a device and print what is playing."""
    print("* Connecting to", conf.address)
    
    atv = await pyatv.connect(conf, loop)
    if atv.service.credentials:
        save_credentials(atv.service.identifier, atv.service.credentials)
    listener = PushUpdatePrinter()
    atv.push_updater.listener = listener
    atv.push_updater.start()

    process = await create_process(f"./run.sh", f"--hostID", f"{conf.identifier}",  f"-i", f"{instance}")
    try:
        print("* Starting to stream")
        await atv.stream.stream_file(process.stdout)
        await asyncio.sleep(0.01)
    except Exception as e:
        print(e)
    finally:
        atv.close()

async def scan(
    loop: asyncio.AbstractEventLoop,
    identifer: str = None
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
    selected_device = await select_to_stream(devices, loop, identifier=identifer)
    pairing_mode = selected_device.services[0].pairing
    if pairing_mode == PairingRequirement.Optional or pairing_mode == PairingRequirement.Mandatory:
        try:
            print("* Attempting to pair to", selected_device.address)
            await pair(selected_device, loop)
        except:
            pass
    await stream_with_push_updates(selected_device, loop)
    return devices
async def select_to_stream(
    devices: List[BaseConfig],
    loop: asyncio.AbstractEventLoop,
    identifier: str = None
):
    """Find a device and print what is playing."""
    known_device = filter(lambda x: x.identifier == identifier, devices)
    if known_device:
        print("Found desired device")
        for d in known_device:
            return d
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

    return device

if __name__ == "__main__":
    LOOP.run_until_complete(scan(LOOP, sys.argv[1]))