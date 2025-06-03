#!/usr/bin/env python3
"""Pymodbus asynchronous Server with updating task Example.

An example of an asynchronous server and
a task that runs continuously alongside the server and updates values.

usage::

    server_updating.py [-h] [--comm {tcp,udp,serial,tls}]
                       [--framer {ascii,rtu,socket,tls}]
                       [--log {critical,error,warning,info,debug}]
                       [--port PORT] [--store {sequential,sparse,factory,none}]
                       [--device_ids DEVICE_IDS]

    -h, --help
        show this help message and exit
    -c, --comm {tcp,udp,serial,tls}
        set communication, default is tcp
    -f, --framer {ascii,rtu,socket,tls}
        set framer, default depends on --comm
    -l, --log {critical,error,warning,info,debug}
        set log level, default is info
    -p, --port PORT
        set port
        set serial device baud rate
    --store {sequential,sparse,factory,none}
        set datastore type
    --device_ids DEVICE_IDS
        set number of devices to respond to

The corresponding client can be started as:
    python3 client_sync.py
"""
import asyncio
import logging
import sys
import datetime

try:
    import server_async  # type: ignore[import-not-found]
except ImportError:
    print("*** ERROR --> THIS EXAMPLE needs the example directory, please see \n\
          https://pymodbus.readthedocs.io/en/latest/source/examples.html\n\
          for more information.")
    sys.exit(-1)

from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)


_logger = logging.getLogger(__name__)


async def updating_task(context):
    """Update values in server.

    This task runs continuously beside the server
    It will increment some values each two seconds.

    It should be noted that getValues and setValues are not safe
    against concurrent use.

    coil (0) - water pump open/close state
    coil (1) - gate open/close state
    ir (0) - water level
    """
    r_coil = 0x1
    w_coil = 0xf
    rw_ir = 0x4

    device_id = 0x00
    address = 0

    # initialise values
    # set waterlevel to 5000 units, pump on, gate closed
    context[device_id].setValues(rw_ir, address, [5000])
    context[device_id].setValues(w_coil, address, [1,0])

    # incrementing loop
    while True:
        await asyncio.sleep(0.5)

        pump, gate = context[device_id].getValues(r_coil, address, 2)
        waterlevel = context[device_id].getValues(rw_ir, address, 1)[0]
        txt = f"{str(datetime.datetime.now())[:-3]} - updating_task: pump: {"on" if pump else "off"}, gate: {"open" if gate else "closed"}, water level: {waterlevel!s}"
        print(txt)
        _logger.debug(txt)
        
        # if pump is on, increase water level by 100 units
        if pump: waterlevel += 100

        # if gate is open, decrease water level by 250 units
        if gate: waterlevel -= 250

        # if waterlevel > 10000, open the gate and turn off the pump
        if waterlevel > 10000:
            pump = 0
            gate = 1
        
        # if waterlevel < 1000, close the gate and turn on the pump
        if waterlevel < 1000:
            pump = 1
            gate = 0

        # ensure waterlevel fits within the modbus register range
        if waterlevel < 0: waterlevel = 0
        if waterlevel > 65535: waterlevel = 65535

        # print flooding alert if water level is greater than 15000
        if waterlevel > 15000:
            txt = f"[ALERT] dam is flooding"
            print(txt)
            _logger.debug(txt)

        # update values
        context[device_id].setValues(w_coil, address, [pump,gate])
        context[device_id].setValues(rw_ir, address, [waterlevel])


def setup_updating_server(cmdline=None):
    """Run server setup."""
    # The datastores only respond to the addresses that are initialized
    # If you initialize a DataBlock to addresses of 0x00 to 0xFF, a request to
    # 0x100 will respond with an invalid address exception.
    # This is because many devices exhibit this kind of behavior (but not all)

    # Continuing, use a sequential block without gaps.
    device_context = ModbusDeviceContext(
        di=ModbusSequentialDataBlock(0x00, [0] * 100),
        co=ModbusSequentialDataBlock(0x00, [0] * 100),
        hr=ModbusSequentialDataBlock(0x00, [0] * 100),
        ir=ModbusSequentialDataBlock(0x00, [0] * 100))
    context = ModbusServerContext(devices=device_context, single=True)
    return server_async.setup_server(
        description="Run asynchronous server.", context=context, cmdline=cmdline
    )


async def run_updating_server(args):
    """Start updating_task concurrently with the current task."""
    task = asyncio.create_task(updating_task(args.context))
    task.set_name("example updating task")
    await server_async.run_async_server(args)  # start the server
    task.cancel()


async def main(cmdline=None):
    """Combine setup and run."""
    run_args = setup_updating_server(cmdline=cmdline)
    await run_updating_server(run_args)


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
