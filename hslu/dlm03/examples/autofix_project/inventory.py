import os
import sys
from typing import List


class Inventory:
    def __init__(self):
        self.items = {}

    def add(self, name, quantity=1):
        if quantity == None:
            quantity = 1
        self.items[name] = self.items.get(name, 0) + quantity

    def remove(self, name, quantity=1):
        try:
            self.items[name] -= quantity
        except:
            print(f"Item not found")
        if self.items.get(name, 0) <= 0:
            self.items.pop(name, None)

    def total(self):
        count = 0
        for name in self.items:
            count += self.items[name]
        return count

    def report(self):
        lines = [f"{name}: {quantity}" for name, quantity in self.items.items()]
        return "\n".join(lines)
