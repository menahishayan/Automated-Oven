import subprocess
import signal
import json
from time import time, sleep
import os

from flask import Flask, request, send_from_directory, render_template, redirect
app = Flask(__name__, static_url_path='')

currentdir = os.path.dirname(os.path.abspath(__file__))
os.chdir(currentdir)

ssid_list = []
wpadir = currentdir + '/wpa/'
testconf = wpadir + 'test.conf'
wpalog = wpadir + 'wpa.log'
wpapid = wpadir + 'wpa.pid'


def getssid():
    global ssid_list
    if len(ssid_list) > 0:
        return ssid_list
    ssid_list = []
    get_ssid_list = subprocess.check_output(('iw', 'dev', 'wlan0', 'scan', 'ap-force'))
    ssids = get_ssid_list.splitlines()
    for s in ssids:
        s = s.strip().decode('utf-8')
        if s.startswith("SSID"):
            a = s.split(": ")
            try:
                ssid_list.append(a[1])
            except:
                pass
    # print(ssid_list)
    ssid_list = sorted(list(set(ssid_list)))
    return ssid_list


wpa_conf_default = """country=IN
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
"""

wpa_conf = wpa_conf_default + """network={
    ssid="%s"
    %s
}"""


def stop_ap(stop):
    if stop:
        subprocess.check_output(['systemctl', "stop", "hostapd", "dnsmasq", "dhcpcd"])
    else:
        subprocess.check_output(['systemctl', "restart", "dnsmasq", "dhcpcd"])
        sleep(5)
        subprocess.check_output(['systemctl', "restart", "hostapd"])


def killPID(pid):
    with open(pid, 'r') as p:
        pid = p.read()
        pid = int(pid.strip())
        os.kill(pid, signal.SIGTERM)


def isConnected():
    stop_ap(True)
    subprocess.Popen(['wpa_supplicant', "-Dnl80211", "-iwlan0", "-c/" + testconf, "-f", wpalog, "-B", "-P", wpapid])

    start = time()

    while time() < start+10:
        sleep(0.5)
        with open(wpalog, 'r') as f:
            content = f.read()
            if "CTRL-EVENT-CONNECTED" in content:
                return True

    killPID(wpapid)

    stop_ap(False)
    return False


def generateCredentials(ssid, password):
    subprocess.Popen("wpa_passphrase {} {} > {}".format(ssid, password, testconf))


@app.route('/')
@app.route('/generate_204')
@app.route('/hotspot-detect.html')
@app.route('/ncsi.txt')
def main():
    return render_template('index.html', ssids=getssid(), message="Connect your oven to the network.")


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


@app.route('/join', methods=['POST'])
def signin():
    try:
        ssid = request.form['ssid']
    except:
        return redirect('/')
    password = request.form['password']

    pwd = 'psk="' + password + '"' if not password == "" else "key_mgmt=NONE"

    generateCredentials(ssid, password)
    if isConnected():
        with open('network_status.json', 'w') as f:
            f.write(json.dumps({'status': 'connected'}))
        with open('wpa.conf', 'w') as f:
            f.write(wpa_conf % (ssid, pwd))

        subprocess.Popen(["./disable_ap.sh"])

        return render_template('index.html', message="Connecting to network. This may take upto 2 minutes.")

    else:
        return render_template('index.html', message="The password was incorrect. Please try again.")


if __name__ == "__main__":
    s = {'status': 'disconnected'}

    if os.path.isfile('network_status.json'):
        s = json.load(open('network_status.json'))

    if isConnected():
        s['status'] = 'connected'
    elif s['status'] == 'connected':
        s['status'] = 'hostapd'

    with open('network_status.json', 'w') as f:
        f.write(json.dumps(s))

    if not s['status'] == 'connected':
        with open('wpa.conf', 'w') as f:
            f.write(wpa_conf_default)
        subprocess.Popen("./enable_ap.sh")
        if not os.path.exists(wpadir):
            os.mkdir(wpadir)
        app.run(host="0.0.0.0", port=80, threaded=True)
