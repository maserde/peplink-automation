
import json
import requests
import os
import urllib3
import time

# Disable SSL warnings for unverified HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PEPLINK_BASE_URL = os.getenv("PEPLINK_BASE_URL")
PEPLINK_USERNAME = os.getenv("PEPLINK_USERNAME")
PEPLINK_PASSWORD = os.getenv("PEPLINK_PASSWORD")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
HASH = None
AUTH_COOKIE = None

class Peplink:
		def __init__(self):
				self.HASH = None
				self.AUTH_COOKIE = None
				self.SYSTEM = {
						"model_name": "Unknown",
						"model_number": "Unknown",
						"firmware_version": "Unknown",
						"serial_number": "Unknown"
				}
				self.WANS = []
				self.MARKED_PASSIVE_WANS = [
						"Wi-Fi WAN on 2.4 GHz",
						"Wi-Fi WAN on 5 GHz",
						"VLAN WAN 1"
				]

		def login(self):
				payload = {
						"username": PEPLINK_USERNAME,
						"password": PEPLINK_PASSWORD,
						"func": "login",
						"hash": True
				}
				response = requests.post(
						f"{PEPLINK_BASE_URL}/cgi-bin/MANGA/api.cgi", data=payload, verify=False)
				data = response.json()
				self.AUTH_COOKIE = response.cookies.get("bauth")
				self.HASH = data["hash"]

		def get_system_summary(self):
				params = {
						"func": "status.system.info",
						"infoType": "device"
				}
				response = requests.get(f"{PEPLINK_BASE_URL}/cgi-bin/MANGA/api.cgi", params=params,
																headers={"Cookie": f"bauth={self.AUTH_COOKIE}"}, verify=False)
				data = response.json()
				self.SYSTEM["model_name"] = data["response"]["device"]["model"]
				self.SYSTEM["model_number"] = data["response"]["device"]["name"]
				self.SYSTEM["firmware_version"] = data["response"]["device"]["firmwareVersion"]
				self.SYSTEM["serial_number"] = data["response"]["device"]["serialNumber"]
				return self.SYSTEM

		def get_wans(self):
				params = {
						"func": "status.wan.connection"
				}
				response = requests.get(f"{PEPLINK_BASE_URL}/cgi-bin/MANGA/api.cgi", params=params,
																headers={"Cookie": f"bauth={self.AUTH_COOKIE}"}, verify=False)
				data = response.json()
				try:
						wans = []
						for key, value in data["response"].items():
								if key.isdigit():
										wans.append(dict(value, **{"id": int(key)}))
				except Exception as e:
						print(f"")
						print(f"[ERROR] There's an error while getting WANs: {str(e)}")
						wans = []
				self.WANS = wans
				return self.WANS

		def print_auth_summary(self):
				print(f"")
				print(f"System Auth Summary:")
				print(f"Auth Cookie: {self.AUTH_COOKIE}")
				print(f"Auth Hash: {self.HASH}")

		def print_system_summary(self):
				print(f"")
				print(f"System Summary:")
				print(f"Model Name: {self.SYSTEM['model_name']}")
				print(f"Model Number: {self.SYSTEM['model_number']}")
				print(f"Firmware Version: {self.SYSTEM['firmware_version']}")
				print(f"Serial Number: {self.SYSTEM['serial_number']}")

		def print_wans_summary(self):
				print(f"")
				print(f"WANs Summary:")
				for wan in self.WANS:
						print(f"ID: {dict.get(wan, 'id') if dict.get(wan, 'id') else 'N/A'}")
						print(
								f"Name: {dict.get(wan, 'name') if dict.get(wan, 'name') else 'N/A'}")
						print(
								f"IP Address: {dict.get(wan, 'ip') if dict.get(wan, 'ip') else 'N/A'}")
						print(f"Enabled: {'YES' if dict.get(wan, 'enable') else 'NO'}")
						print(
								f"Status: {dict.get(wan, 'message') if dict.get(wan, 'message') else 'N/A'}")
						print(f"")

		def get_wan_by_id(self, wan_id):
				for wan in self.WANS:
						if dict.get(wan, 'id') == wan_id:
								return wan
				return None

		def switch_wan_status_by_id(self, wan_id, status):
				wan = self.get_wan_by_id(wan_id)
				if wan:
						current_status = "enabled" if dict.get(
								wan, 'enable') else "disabled"
						new_status = "enabled" if status.lower() == "enable" else "disabled"
						if (current_status == new_status):
								print(f"")
								print(
										f"[INFO] {wan['name']} WAN status is already {current_status}. Skipping ...")
								return

						print(f"")
						print(
								f"[WARN] Switch {wan['name']} WAN status from {current_status} to {new_status} ...")
						payload = {
								"func": "config.wan.connection.priority",
								"instantActive": True,
								"list": [{
										"connId": dict.get(wan, 'id'),
										"enable": True if status.lower() == "enable" else False
								}]
						}
						headers = {
								"Content-Type": "application/json; charset=UTF-8",
								"Cookie": f"bauth={self.AUTH_COOKIE}"
						}
						try:
								response = requests.post(
										f"{PEPLINK_BASE_URL}/cgi-bin/MANGA/api.cgi", json=payload, headers=headers, verify=False)
								data = response.json()
								if not data["stat"] == 'ok':
										raise Exception(
												"Failed switch WAN status. Non 'ok' status.")
						except Exception as e:
								print(f"")
								print(
										f"[ERROR] There's an error while switching {wan['name']} WAN status: {str(e)}")
						
						try:
								self.send_webhook("WAN Disabled", f"{wan['name']} is disabled due to internet connectivity issue. The expected status should be 'Connected' but it is currently '{wan['message']}'.")
						except Exception as e:
								print(f"")
								print(f"[ERROR] There's an error while sending webhook: {str(e)}")

		def send_webhook(self, type, message):
				payload = {
						"type": type,
						"message": message
				}
				try:
					requests.post(WEBHOOK_URL, json=payload)
				except Exception as e:
						print(f"")
						print(f"[ERROR] There's an error while sending webhook: {str(e)}")

		def get_disconnected_wans(self):
				disconnected_wans = []
				for wan in self.WANS:
						allowed_statuses = [
								'Connected',
								'Connecting...',
								'Obtaining IP Address...'
						]
						if not dict.get(wan, 'message') in allowed_statuses and dict.get(wan, 'name') not in self.MARKED_PASSIVE_WANS:
								disconnected_wans.append(wan)
								continue
				return disconnected_wans


def main():
		peplink = Peplink()
		peplink.login()
		peplink.print_auth_summary()
		peplink.get_system_summary()
		peplink.get_wans()
		peplink.print_system_summary()
		peplink.print_wans_summary()
		disconnected_wans = peplink.get_disconnected_wans()
		if len(disconnected_wans) > 0:
				for wan in disconnected_wans:
						peplink.switch_wan_status_by_id(wan['id'], "disable")
		else:
				print(f"")
				print(f"[INFO] All WANs are connected")


if __name__ == "__main__":
		main()
