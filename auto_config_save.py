
from netmiko import ConnectHandler
from yaml import safe_load
from datetime import datetime

def get_run():
    with open("devices.yaml") as file:
        device_details=safe_load(file)

    for device_list,device_info in device_details.get("devices").items():
        device={
            "device_type":"cisco_ios",
            "host":device_info.get("ip"),
            "username":device_details['global'].get("username"),
            "password":device_details['global'].get("password"),
            "secret":device_details['global'].get("secret")
        }
        print(device)
        conn=ConnectHandler(**device)
        conn.enable()
        run_config=conn.send_command("sh run",expect_string=r"#",read_timeout=120)
        #conn.save_config()
        with open(f"{device_list}{str(datetime.now().isoformat()).replace(':','').replace('.','_')}","w") as file:
            file.write(run_config)
        conn.disconnect()