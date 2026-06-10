from netmiko import  ConnectHandler
from yaml import safe_load
from jinja2 import Environment, FileSystemLoader
env = Environment(loader = FileSystemLoader('templates'))
template = env.get_template('basic.jinja')
with open("config\device_configs.yaml","r") as file:
    configs=safe_load(file)
for device_name,device_data in configs.get('devices').items():
    output = template.render(
        device=device_name,
        global_config=configs["global"],
        **device_data
    )
    with open(f"{device_name}.cfg", "w") as file:
        file.write(output)


"""    device = {
        "device_type": "cisco_ios",
        "host": device_data.get("management_ip"),
        "username": configs["global"].get("username"),
        "password": configs["global"].get("password"),
        "secret": configs["global"].get("secret")
    }
"""

