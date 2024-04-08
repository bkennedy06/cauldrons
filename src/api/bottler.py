import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}") # update inventory with potions made
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")
    with db.engine.begin() as connection:
        curr_green_ml = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).first()[1]
        curr_green_potions = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).first()[0]

        net_green_ml = 0
        net_green_pot = 0
        for p_inv in potions_delivered:
            if p_inv.potion_type == [0, 100, 0, 0]: # green
                net_green_ml += (100 * p_inv.quantity)
                net_green_pot += p_inv.quantity # add total number of green potions
        net_green_ml += curr_green_potions

        net_green_ml = curr_green_ml - net_green_ml # subtracting ml from total, conversion to potions

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :newGml"), newGml=net_green_ml)
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = :newPot"), newPot=net_green_pot)


    return "OK"

@router.post("/plan") # request potions made
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    
    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    with db.engine.begin() as connection:
        green_ml_available = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).first()[0]
        new_potions = green_ml_available // 100 # or however much mL per potion
        
    return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": new_potions,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())