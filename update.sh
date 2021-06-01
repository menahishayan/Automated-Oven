#!/bin/bash

sudo systemctl stop oven
git pull
sudo systemctl start oven