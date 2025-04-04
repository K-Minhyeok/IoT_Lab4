from flask import Flask, render_template, request, jsonify
import subprocess
import os
import time

app = Flask(__name__)

# Scan available WiFi networks
def scan_wifi():
    result = subprocess.run(["iwlist", "wlan0", "scan"], capture_output=True, text=True)
    networks = []
    for line in result.stdout.split("\n"):
        if "ESSID" in line:
            ssid = line.split(":")[1].strip().strip('"')
            if ssid:  # Avoid empty SSIDs
                networks.append(ssid)
    return networks

# Connect to the specified WiFi
def connect_wifi(ssid, password):
    print(f"[DEBUG] Stopping AP services and preparing for connection...")

    # Stop AP services
    subprocess.run(["sudo", "systemctl", "stop", "hostapd"])
    subprocess.run(["sudo", "systemctl", "stop", "dnsmasq"])

    # Set wlan0 to managed mode
    subprocess.run(["sudo", "ip", "link", "set", "wlan0", "down"])
    subprocess.run(["sudo", "iw", "wlan0", "set", "type", "managed"])
    subprocess.run(["sudo", "ip", "link", "set", "wlan0", "up"])

    # Kill existing wpa_supplicant instances
    subprocess.run(["sudo", "pkill", "wpa_supplicant"])

    # Generate config using wpa_passphrase
    result = subprocess.run(
        ["wpa_passphrase", ssid, password],
        capture_output=True,
        text=True
    )
    config = f"""ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US
{result.stdout}
"""

    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as f:
        f.write(config)

    # Start fresh wpa_supplicant in background
    subprocess.run([
        "sudo", "wpa_supplicant", "-B", "-i", "wlan0", "-c", "/etc/wpa_supplicant/wpa_supplicant.conf"
    ])

    # Start DHCP client
    subprocess.run(["sudo", "dhclient", "wlan0"])

    # Poll for connection
    for _ in range(10):
        result = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True)
        current_ssid = result.stdout.strip()
        if current_ssid == ssid:
            print("[DEBUG] Connected to:", current_ssid)
            return True
        time.sleep(1)

    print("[DEBUG] Failed to connect")
    return False

@app.route("/")
def index():
    networks = scan_wifi()
    return render_template("index.html", networks=networks)

@app.route("/connect", methods=["POST"])
def connect():
    ssid = request.form["ssid"]
    password = request.form["password"]

    print(f"[DEBUG] Trying to connect to SSID: '{ssid}' with password: '{password}'")

    success = connect_wifi(ssid, password)
    return jsonify({"success": success})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
