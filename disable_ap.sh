#!/bin/bash

sudo systemctl stop hostapd dnsmasq dhcpcd

sudo cp config/hostapd.disabled /etc/default/hostapd
sudo cp config/dhcpcd.conf.disabled /etc/dhcpcd.conf
sudo cp config/dnsmasq.conf.disabled /etc/dnsmasq.conf

# load wlan configuration
sudo cp wpa.conf /etc/wpa_supplicant/wpa_supplicant.conf

sudo systemctl daemon-reload
sudo systemctl start dhcpcd

