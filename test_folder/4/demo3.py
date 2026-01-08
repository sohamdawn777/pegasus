import json

with open("config.json") as f:
    config = json.load(f)

print("Loaded config:", config)

