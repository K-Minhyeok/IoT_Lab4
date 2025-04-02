from flask import Flask, render_template, request, jsonify
import subprocess
import os

app = Flask(__name__)

# WiFi 스캔 함수
def scan_wifi():
    result = subprocess.run(["iwlist", "wlan0", "scan"], capture_output=True, text=True)
    networks = []
    for line in result.stdout.split("\n"):
        if "ESSID" in line:
            ssid = line.split(":")[1].strip().strip('"')
            networks.append(ssid)
    return networks

# WiFi 연결 함수
def connect_wifi(ssid, password):
    config = f"""
    ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
    update_config=1
    country=US

    network={{
        ssid="{ssid}"
        psk="{password}"
        key_mgmt=WPA-PSK
    }}
    """
    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as f:
        f.write(config)

    subprocess.run(["sudo", "wpa_cli", "-i", "wlan0", "reconfigure"])
    return True

# 메인 페이지
@app.route("/")
def index():
    networks = scan_wifi()
    return render_template("index.html", networks=networks)

# WiFi 연결 요청 처리
@app.route("/connect", methods=["POST"])
def connect():
    ssid = request.form["ssid"]
    password = request.form["password"]
    success = connect_wifi(ssid, password)
    return jsonify({"success": success})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
