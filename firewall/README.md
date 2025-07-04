# Firewall VM

## Installation

1. Install pfsense [here](https://www.pfsense.org/download/), instructions [here](https://docs.netgate.com/pfsense/en/latest/install/index.html).
    - We use pfsense 2.8.0 in the given VM

2. Attach network adapters to the VM.
    - Firewall VM 1:
        - <ins>Firewall 1 Adapter 1</ins>: 192.168.60.0/24
        - <ins>Firewall 1 Adapter 2</ins>: 192.168.65.0/24
        - <ins>Firewall 1 Adapter 3</ins>: NAT
    - Firewall VM 2:
        - <ins>Firewall 2 Adapter 1</ins>: 192.168.65.0/24
        - <ins>Firewall 2 Adapter 1</ins>: 192.168.75.0/24 (if using simulator) OR bridged adapter (select your ethernet port, if using the in person setup)

3. In pfsense, change the interfaces to the following.
    - Firewall VM 1:
        - WAN: NAT adapter `em2`
        - LAN: first host-only ethernet adapter `em0`, IP address 192.168.60.100
        - LAN1: second host-only ethernet adapter `em1`, IP address 192.168.65.100
    - Firewall VM 2:
        - WAN: first host-only ethernet adapter `em0`, IP address 192.168.65.101
        - LAN: second host-only ethernet adapter `em1`, IP address 192.168.75.101

4. [Only for Firewall VM 1] Install `snort` under package manager. 

5. [Only for Firewall VM 1] Add our custom rules. 
    - Go to `Snort Interfaces > LAN > LAN Rules`

6. [Only for Firewall VM 1] Disable all rules apart from our custom rules, and the modbus and ARP spoofing rules.

7. [Only for Firewall VM 1] Enable Inline IPS mode

8. [Only for Firewall VM 1] Enable ARP Spoofing Detection and Modbus Detection in the LAN's `preprocs` settings. Also include the MAC to IP pairings of the SCADA (192.168.60.10) and Firewall VM 1's 192.168.60.100 interface.

