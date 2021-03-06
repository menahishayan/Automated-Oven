import logging
import subprocess
import signal
import json
from time import time, sleep
from re import findall
import os

# from flask import Flask, request, send_from_directory, render_template, redirect
# app = Flask(__name__, static_url_path='')

currentdir = os.path.dirname(os.path.abspath(__file__))
os.chdir(currentdir)

# ssid_list = []
wpadir = currentdir + '/wpa/'
testconf = wpadir + 'test.conf'
wpalog = wpadir + 'wpa.log'
wpapid = wpadir + 'wpa.pid'

# logger_format = '%(asctime)s %(message)s'
# logging.basicConfig(format=logger_format, level=logging.INFO, datefmt="%H:%M:%S", filename='./netdaemon.log', filemode='w')

# def getssid():
#     global ssid_list
#     if len(ssid_list) > 0:
#         return ssid_list
#     ssid_list = []
#     get_ssid_list = subprocess.check_output(('iw', 'dev', 'wlan0', 'scan', 'ap-force'))
#     ssids = get_ssid_list.splitlines()
#     for s in ssids:
#         s = s.strip().decode('utf-8')
#         if s.startswith("SSID"):
#             a = s.split(": ")
#             try:
#                 ssid_list.append(a[1])
#             except:
#                 pass
#     # print(ssid_list)
#     ssid_list = sorted(list(set(ssid_list)))
#     return ssid_list


wpa_conf_default = """country=IN
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
"""

wpa_conf = wpa_conf_default + """network={
    ssid="%s"
    %s
}"""


# def killPID(pid):
#     with open(pid, 'r') as p:
#         pid = p.read()
#         pid = int(pid.strip())
#         os.kill(pid, signal.SIGTERM)


# def generateCredentials(ssid, password):
#     result = subprocess.check_output(['wpa_passphrase', ssid, password])
#     with open(testconf, 'w') as f:
#         f.write(result.decode('utf-8'))

# def connect():
#     for _file in [wpalog, wpapid]:
#         if os.path.exists(_file):
#             os.remove(_file)

#     subprocess.Popen(["./disable_ap.sh"])

#     subprocess.Popen(['wpa_supplicant', "-Dnl80211", "-iwlan0", "-c/" + testconf, "-f", wpalog, "-B", "-P", wpapid])
#     start = time()
#     while time() < start+10:
#         sleep(0.5)
#         with open(wpalog, 'r') as f:
#             content = f.read()
#             if "CTRL-EVENT-CONNECTED" in content or "Match already configured" in content:
#                 logging.info("connect: True")
#                 return True

#     killPID(wpapid)

#     logging.info("connect: False")
#     logging.info("connect: Enable AP")
#     subprocess.Popen(["./enable_ap.sh"])
#     return False

def isConnected():
    if not os.path.exists(testconf):
        return False

    for _ in range(2):
        result = subprocess.check_output(['iwconfig', 'wlan0'])
        if len(findall(r'\"(.+?)\"', result.split(b'\n')[0].decode('utf-8'))) > 0:
            return True
        sleep(2)

    return False

# def shutdown_server():
#     func = request.environ.get('werkzeug.server.shutdown')
#     if func is None:
#         raise RuntimeError('Not running with the Werkzeug Server')
#     func()


# @app.route('/')
# @app.route('/generate_204')
# @app.route('/hotspot-detect.html')
# @app.route('/ncsi.txt')
# def main():
#     return render_template('index.html', ssids=getssid(), message="Connect your oven to the network.")

# @app.route('/jsonReq')
# def jsonReq():
#     return json.dumps(getssid())

# @app.route('/static/<path:path>')
# def send_static(path):
#     return send_from_directory('static', path)


# @app.route('/join', methods=['POST'])
# def signin():
#     ssid = request.form['ssid']
#     password = request.form['password']

#     pwd = 'psk="' + password + '"' if not password == "" else "key_mgmt=NONE"

#     generateCredentials(ssid, password)
#     if connect() or isConnected():
#         logging.info("signin: isConnected True")
#         with open('network_status.json', 'w') as f:
#             f.write(json.dumps({'status': 'connected'}))
#         with open('wpa.conf', 'w') as f:
#             f.write(wpa_conf % (ssid, pwd))
        
#         shutdown_server()
#         return render_template('index.html', message="Connected.")

#     else:
#         logging.info("signin: isConnected False")
#         return render_template('index.html', message="The password was incorrect. Please try again.")


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
