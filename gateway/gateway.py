import asyncio
import logging
import datetime
from pathlib import Path
import socket

from asyncua import Server, ua
import pymodbus.client as modbusClient
from pymodbus import ModbusDeviceIdentification
from pymodbus import __version__ as pymodbus_version
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)

from asyncua.server.users import UserRole, User
from asyncua.crypto.cert_gen import setup_self_signed_certificate
from cryptography.x509.oid import ExtendedKeyUsageOID


_logger = logging.getLogger(__file__)
logging.getLogger('asyncua').setLevel("ERROR")

ENABLE_SECURITY = True


def setup_modbus_client(description: str | None =None, cmdline: str | None = None) -> modbusClient.ModbusBaseClient:
    """Run modbus client setup."""
    client: modbusClient.ModbusBaseClient | None = None
    client = modbusClient.AsyncModbusTcpClient(
        '192.168.75.5',
        port='502', 
        framer='socket',
        timeout=10,
        retries=3,
        reconnect_delay=1,
        reconnect_delay_max=10,
    )

    _logger.info("### Setup modbus client with PLC.")

    return client


def setup_modbus_server():
    """Run modbus server setup."""
    device_context = ModbusDeviceContext(
        di=ModbusSequentialDataBlock(0x00, [0] * 100),
        co=ModbusSequentialDataBlock(0x00, [0] * 100),
        hr=ModbusSequentialDataBlock(0x00, [0] * 100),
        ir=ModbusSequentialDataBlock(0x00, [0] * 100))
    
    context = ModbusServerContext(devices=device_context, single=True)
    identity = ModbusDeviceIdentification(
        info_name={
            "VendorName": "Pymodbus",
            "ProductCode": "PM",
            "VendorUrl": "https://github.com/pymodbus-dev/pymodbus/",
            "ProductName": "Pymodbus Server",
            "ModelName": "Pymodbus Server",
            "MajorMinorRevision": pymodbus_version,
        }
    )

    address = ('', '502')
    server_task = asyncio.create_task(
        StartAsyncTcpServer(
            context=context,
            identity=identity,
            address=address,
            framer="socket" 
        )
    )
    _logger.info("### Setup modbus gateway server.")
    return context, server_task


# initialise users
users_db =  {
    'fuxa': 'fuxa'
}

class UserManager:
    def get_user(self, iserver, username=None, password=None, certificate=None):
        if username in users_db and password == users_db[username]:
            return User(role=UserRole.User)
        return None


async def setup_security():
    """Setup certificates for OPC UA security."""
    # create certificates directory if it doesn't exist
    CERTIFICATES_DIR = Path("certificates")
    CERTIFICATES_DIR.mkdir(exist_ok=True)
    
    # certificate paths
    server_cert = CERTIFICATES_DIR / "server-certificate.der"
    server_private_key = CERTIFICATES_DIR / "server-private-key.pem"
    
    # initialise server with users
    server = Server(user_manager=UserManager())
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/")
    server.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt, ua.SecurityPolicyType.NoSecurity])

    # get hostname for certificate
    host_name = socket.gethostname()
    server_app_uri = f"gateway@{host_name}"

    # generate server certificate if it doesn't exist or is expired
    await setup_self_signed_certificate(
        server_private_key,
        server_cert,
        server_app_uri,
        host_name,
        [ExtendedKeyUsageOID.CLIENT_AUTH, ExtendedKeyUsageOID.SERVER_AUTH],
        {
            "countryName": "SG",
            "stateOrProvinceName": "SG",
            "localityName": "Singapore",
            "organizationName": "Foo Bar Inc",
            "commonName": host_name,
        },
    )

    # load server certificate and private key
    await server.load_certificate(str(server_cert))
    await server.load_private_key(str(server_private_key))
    
    _logger.info(f"Server certificate created at: {server_cert}")
    _logger.info(f"Server private key created at: {server_private_key}")
    
    return server


async def setup_opcua_server():
    '''Run OPC UA server setup.'''

    if ENABLE_SECURITY:
        # setup our server with Basic256Sha256_SignAndEncrypt security
        server = await setup_security()
    else:
        # setup our server without any security
        server = Server()
        await server.init()
        server.set_endpoint("opc.tcp://0.0.0.0:4840/")
        server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    # set up our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # create objects and variables
    myobj = await server.nodes.objects.add_object(idx, "modbus")
    pump = await myobj.add_variable(idx, "pump", False)
    gate = await myobj.add_variable(idx, "gate", False)
    waterlevel = await myobj.add_variable(idx, "water_level", ua.Variant(0, ua.VariantType.UInt16))

    # Set variables to be writable by clients
    await pump.set_writable()
    await gate.set_writable()
    _logger.info("### Setup OPC UA server.")

    return server, pump, gate, waterlevel


async def main():
    # setup opc ua server
    server, pump, gate, waterlevel = await setup_opcua_server()
    
    # setup modbus client to interact with PLC
    client = setup_modbus_client()

    # setup and run modbus gateway server
    mb_context, modbus_server_task = setup_modbus_server()

    try:
        await client.connect()
        assert client.connected
        await server.start()

        last_pump_val = 0
        last_gate_val = 0

        device_id = 0x00
        r_coil = 0x1
        w_coil = 0xf
        rw_ir = 0x4

        while True:
            await asyncio.sleep(0.3)

            # get values from PLC
            rr = await client.read_coils(0, count=2)
            pump_mb, gate_mb = rr.bits[0], rr.bits[1]

            rr = await client.read_input_registers(0, count=1)
            waterlevel_mb = rr.registers[0]


            # check for changes from OPC UA client
            new_pump_opc = await pump.get_value()
            new_gate_opc = await gate.get_value()
            
            # check for changes from Modbus gateway server
            new_pump_mb, new_gate_mb = mb_context[device_id].getValues(r_coil, 0, 2)


            # write to PLC if there is a change (priority: OPC UA > Modbus gateway > PLC)
            if (last_pump_val != new_pump_opc): # OPC UA client changed pump value                
                pump_mb = True if new_pump_opc else False
                await client.write_coil(0,new_pump_opc)
                _logger.info(f"OPC UA client changed pump to: {pump_mb!s}")
            
            elif (last_pump_val != new_pump_mb): # Modbus gateway client changed pump value
                pump_mb = True if new_pump_mb else False
                await client.write_coil(0,new_pump_mb)
                _logger.info(f"Modbus client changed pump to: {pump_mb!s}")

            if (last_gate_val != new_gate_opc): # OPC UA client changed gate value
                gate_mb = True if new_gate_opc else False
                await client.write_coil(1,new_gate_opc)
                _logger.info(f"OPC UA client changed gate to: {gate_mb!s}")
            
            elif (last_gate_val != new_gate_mb): # Modbus gateway client changed gate value
                gate_mb = True if new_gate_mb else False
                await client.write_coil(1,new_gate_mb)
                _logger.info(f"Modbus client changed gate to: {gate_mb!s}")


            # writes values to OPC
            await pump.write_value(pump_mb)
            await gate.write_value(gate_mb)
            await waterlevel.write_value(waterlevel_mb, ua.VariantType.UInt16)

            # save the last value
            last_pump_val = pump_mb
            last_gate_val = gate_mb

            # update modbus gateway server with new values
            mb_context[device_id].setValues(w_coil, 0, [pump_mb,gate_mb])
            mb_context[device_id].setValues(rw_ir, 0, [waterlevel_mb])

            txt = f"{str(datetime.datetime.now())[:-3]} - pump: {"on" if pump_mb else "off"}, gate: {"open" if gate_mb else "closed"}, water level: {waterlevel_mb!s}"
            print(txt)
            
    finally:
        client.close()
        await server.stop()
        modbus_server_task.cancel()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)
