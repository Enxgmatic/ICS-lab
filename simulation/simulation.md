# Simulation

The VM uses Ubuntu 24.04.

## Installation

1. Clone the repo

```sh
sudo apt-get update
sudo apt install -y git
git clone xx
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
sudo cp simulation.service /lib/systemd/system/
sudo systemctl enable simulation.service
sudo systemctl start simulation.service
```

4. Adjust network adapters