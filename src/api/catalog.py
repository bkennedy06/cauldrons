import sqlalchemy
from src import database as db
from fastapi import APIRouter
import json

router = APIRouter()

# Offer up only the available green potions in global_inventory
# Current (num_green_potions, green_ml, gold)
@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalogue = []
    with db.engine.begin() as connection:
        potions = connection.execute(sqlalchemy.text("SELECT * FROM potions"))
        for potion in potions:
            type = potion[0]
            quantity = potion[1]
            price = potion[2]

            sale = {
                "sku": skuer(potion),
                "name": namer(potion),
                "quantity": quantity,
                "price": price,
                "potion_type": type,
            }
            catalogue.append(sale)

    return catalogue

def skuer(potion):
    type = json.loads(potion[0])
    if type[0] == 100:
        return "Red_Potion"
    elif type[1] == 100:
        return "Green_Potion"
    elif type[2] == 100:
        return "Blue_Potion"
    else:
        return "Custom_Potion_" + potion[0]

def namer(potion):
    type = json.loads(potion[0])
    if type[0] == 100:
        return "Red Potion"
    elif type[1] == 100:
        return "Green Potion"
    elif type[2] == 100:
        return "Blue Potion"
    else:
        return "Custom Potion: " + potion[0]