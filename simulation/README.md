# Simulation VM

The VM provided uses [Ubuntu Server 24.04.2](https://ubuntu.com/download/server).

The VM runs [`simulation.py`](simulation.py).

## Installation

0. Please attach a NAT adapter as adapter 1 (this will be changed later)

1. Clone the repo

```sh
git clone https://github.com/Enxgmatic/ICS-lab
```

2. Run the installation script [`install.sh`](install.sh) for the simulation

<!-- > [!NOTE]
> This will delete the other folders in this repo, leaving only the simulation. -->

```sh
cd ICS-lab
sudo ./simulation/install.sh
```

3. To ensure the simulation runs on startup, set up a systemd service.

> [!IMPORTANT]
> Please adjust `ExecStart` and `WorkingDirectory` based on your installation path.

```sh
cd simulation
sudo cp simulation.service /lib/systemd/system/
sudo systemctl enable simulation.service
sudo systemctl start simulation.service
```

4. Adjust network interface settings. 
    - Create the Host-only ethernet adapters if you have not done so (as specified in [`README.md`](../README.md))
    - Remove the NAT adapter and attach the 192.168.75.0/24 Host-only ethernet adapter as adapter 1.
    - Run the following commands below.

> ![IMPORTANT]
> You may need to change the name of the Ethernet interface in [`99_config.yaml`](99_config.yaml).
> Identify the name by running `ip a`.
> In this case, we assume it is `enp0s3`.

```sh
# edit the ethernet interface names in 99_config.yaml file if needed, based on this output
ip a

# Change the network configuration
sudo cp 99_config.yaml /etc/netplan/

# Apply changes
sudo netplan apply
```
