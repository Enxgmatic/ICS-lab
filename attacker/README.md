# Attacker VM

We are using a Kali Linux VM.

## Installation

0. Please attach a NAT adapter as adapter 2

1. Clone the repo

```sh
git clone https://github.com/Enxgmatic/ICS-lab
```

## Installation - Command Injection

1. Install pymodbus 4.0.0

```sh
cd ICS-lab
sudo ./attacker/install.sh
```

## Installation - MiTM with ARP spoofing

1. Enable ip forwarding

```sh
sudo echo 1 > /proc/sys/net/ipv4/ip_forward
```

2. Prepare filters

```sh
cd attacker/filters
sudo mkdir /usr/share/ettercap/attacks
sudo cp *.ef /usr/share/ettercap/attacks
```

3. If you need to create more filters

```sh
etterfilter -o <name>.ef <name>.filter
```

## Installation - Network Adapters

1. Create the Host-only ethernet adapters if you have not done so (as specified in [`README.md`](../README.md))

2. Attach the 192.168.65.0/24 Host-only ethernet adapter as adapter 1. Attach the NAT adapter as adapter 2.

3. Under `Advanced Network Configuration`, edit `Wired Connection 1`, and set the VM to have a static IP address of `192.168.60.111/24`. Also add a route to `192.168.65.0/24` via `192.168.60.100`.
