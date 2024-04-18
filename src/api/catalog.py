import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()

# Offer up only the available green potions in global_inventory
# Current (num_green_potions, green_ml, gold)
@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        num_green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).first()[0]
        num_red_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).first()[0]
        num_blue_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).first()[0]
    
    catalogue = []
    gpot = {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": num_green_potions,
                "price": 50, # originally 50
                "potion_type": [0, 100, 0, 0], # r g b, and dark
            }
    rpot = {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": num_red_potions,
                "price": 50, # originally 50
                "potion_type": [100, 0, 0, 0], # r g b, and dark
            }
    bpot = {
                "sku": "BLUE_POTION_0",
                "name": "blue potion",
                "quantity": num_blue_potions,
                "price": 50, # originally 50
                "potion_type": [0, 0, 100, 0], # r g b, and dark
            }

    if num_green_potions > 0:
        catalogue.append(gpot)
    if num_red_potions > 0:
        catalogue.append(rpot)
    if num_blue_potions > 0:
        catalogue.append(bpot)

    return catalogue
