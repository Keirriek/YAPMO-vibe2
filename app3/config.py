# https://ireneburresi.dev/singleton-pattern

import json5 as json
import globals

def read_config():
    try:
        with open('conf.json') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def write_config(js):
    with open('conf.json', 'w') as f:
        json_str = json.dumps(js, indent=4)
        f.write(json_str)
    
def init_config():
    globals.config_data=read_config()

def get_config_par(s):
    return globals.config_data[s]

def set_config_par(key, value):
    globals.config_data[key] = value

