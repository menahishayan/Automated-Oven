import subprocess
import signal
import json
from time import time, sleep
from re import findall
import os


class Network:
    def __init__(self, e):
        self.s = json.load(open('network_status.json'))
        self.e = e

        self.wpa_conf_default = """country=IN
        ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
        update_config=1
        """

        self.wpa_conf = self.wpa_conf_default + """network={
            ssid="%s"
            %s
        }"""

        currentdir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(currentdir)
        self.ssid_list = []
        self.wpadir = currentdir + '/wpa/'
        self.testconf = self.wpadir + 'test.conf'
        self.wpalog = self.wpadir + 'wpa.log'
        self.wpapid = self. wpadir + 'wpa.pid'
        self.e.log("Network: Connecting")

    async def getSSIDs(self):
        ssid_list = []
        get_ssid_list = subprocess.check_output(('sudo', 'iw', 'dev', 'wlan0', 'scan', 'ap-force'))
        ssids = get_ssid_list.splitlines()
        for s in ssids:
            s = s.strip().decode('utf-8')
            if s.startswith("SSID"):
                a = s.split(": ")
                try:
                    ssid_list.append(a[1])
                except:
                    pass
        self.ssid_list = sorted(list(set(ssid_list)))
        return self.ssid_list

    def killPID(self, pid):
        with open(pid, 'r') as p:
            pid = p.read()
            pid = int(pid.strip())
            os.kill(pid, signal.SIGTERM)

    def generateCredentials(self, ssid, password):
        result = subprocess.check_output(['wpa_passphrase', ssid, password])
        subprocess.Popen(["sudo","chown","-R", "pi", "/home/pi/OS/wpa", "/home/pi/OS/wpa.conf"])
        with open(self.testconf, 'w') as f:
            f.write(result.decode('utf-8'))

    def connect(self):
        for _file in [self.wpalog, self.wpapid]:
            if os.path.exists(_file):
                os.remove(_file)

        subprocess.Popen(["./disable_ap.sh"])

        subprocess.Popen(['sudo', 'wpa_supplicant', "-Dnl80211", "-iwlan0", "-c/" + self.testconf, "-f", self.wpalog, "-B", "-P", self.wpapid])
        subprocess.Popen(["sudo","chown","-R", "pi", "/home/pi/OS/wpa", "/home/pi/OS/wpa.conf"])
        start = time()
        while time() < start+10:
            sleep(0.5)
            with open(self.wpalog, 'r') as f:
                content = f.read()
                if "CTRL-EVENT-CONNECTED" in content or "Match already configured" in content:
                    return True

        self.killPID(self.wpapid)

        subprocess.Popen(["./enable_ap.sh"])
        return False

    async def isConnected(self):
        if not os.path.exists(self.testconf):
            return False

        for _ in range(2):
            result = subprocess.check_output(['iwconfig', 'wlan0'])
            if len(findall(r'\"(.+?)\"', result.split(b'\n')[0].decode('utf-8'))) > 0:
                return True
            sleep(2)

        return False

    async def joinNetwork(self, ssid, password):
        try:
            self.s['status'] = 'connecting'
            pwd = 'psk="' + password + '"' if not password == "" else "key_mgmt=NONE"

            self.generateCredentials(ssid, password)
            if self.connect() or await self.isConnected():
                self.s['status'] = 'connected'

                with open('network_status.json', 'w') as f:
                    f.write(json.dumps({'status': 'connected'}))

                with open('wpa.conf', 'w') as f:
                    f.write(self.wpa_conf % (ssid, pwd))

                return True

            else:
                self.s['status'] = 'hostapd'
                return False
        except Exception as e:
            self.e.err(e)
            return False

    async def get(self):
        return self.s['status']
