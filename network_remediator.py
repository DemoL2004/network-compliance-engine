import logging
from json import load
from yaml import safe_load
from netmiko import ConnectHandler

logger = logging.getLogger("remediator")
def remediate():
    with open("remediate_status/latest.json", "r") as file:
        remdeiate=load(file)

    with open("devices.yaml", "r") as file:
        device_details=safe_load(file)
    if remdeiate:
        for device_to_remediate in remdeiate:

            if remdeiate[device_to_remediate]:
                device = {
                    "device_type": "cisco_ios",
                    "host": device_details["devices"][device_to_remediate].get("ip"),
                    "username":  device_details['global'].get("username"),
                    "password": device_details['global'].get("password"),
                    "secret": device_details['global'].get("secret")
                }
                try:
                    logger.info(f"STARTING REMEDIATION FOR {device_to_remediate}")
                    conn = ConnectHandler(**device)
                    conn.enable()
                    conn.send_config_set(remdeiate[device_to_remediate])
                    conn.disconnect()
                    logger.info(f"REMEDIATION DONE FOR {device_to_remediate}")
                except Exception as e:
                    logger.exception(f"ERROR {e} WHILE REMEDIATION FOR {device_to_remediate}")