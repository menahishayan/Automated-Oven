#!/bin/bash

cd /home/pi/OS
sudo systemctl stop oven
git pull
sudo systemctl start oven