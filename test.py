import json

# Open the file and load the data
with open('dilution_config.json', 'r') as f:
    config = json.load(f)

# Access data like a dictionary
print(config)
print(config["stock_name"])