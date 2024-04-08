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
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        num_green_potions = result.first()[0] # result is a cursorType and needs those accessors
        
    return [
            {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": num_green_potions,
                "price": 30, # originally 50
                "potion_type": [0, 100, 0, 0], # r g b, and dark
            }
        ]
