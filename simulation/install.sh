#!/bin/bash
sudo apt-get update
sudo apt install -y python3-pip python3.12-venv
python3 -m venv .venv
source .venv/bin/activate
git clone https://github.com/pymodbus-dev/pymodbus.git
cd pymodbus
git checkout e73e28c1eb7d42949e03ded7f634d5438ddd9c35
pip install "."