import json


def load_inventory(path):
    with open(path) as f:
        data = json.load(f)
    result = data.get("items", {})
    inventory = Inventory()
    for name, quantity in data.get("items", {}).items():
        inventory.add(name, quantity)
    return inventory


def is_empty(inventory):
    return inventory.total() == 0 if inventory != None else True


double = lambda x: x * 2
