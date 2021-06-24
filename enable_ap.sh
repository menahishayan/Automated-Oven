#!/bin/bash

# sleep 3

# enable the AP

sudo systemctl stop hostapd dnsmasq dhcpcd

sudo cp config/hostapd /etc/default/hostapd
sudo cp config/dhcpcd.conf /etc/dhcpcd.conf
sudo cp config/dnsmasq.conf /etc/dnsmasq.conf

# load wan configuration
sudo cp wpa.conf /etc/wpa_supplicant/wpa_supplicant.conf

sudo systemctl start hostapd dnsmasq dhcpcd

# sudo reboot now
