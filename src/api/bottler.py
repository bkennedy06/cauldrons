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

        net_green_ml = 0
        net_green_pot = 0
        net_red_ml = 0
        net_red_pot = 0
        net_blue_ml = 0
        net_blue_pot = 0
        for p_inv in potions_delivered:
            if p_inv.potion_type == [0, 100, 0, 0]: # green
                net_green_ml += (100 * p_inv.quantity)
                net_green_pot += p_inv.quantity # add total number of green potions
            elif p_inv.potion_type == [100, 0, 0, 0]: # red
                net_red_ml += (100 * p_inv.quantity)
                net_red_pot += p_inv.quantity # add total number of green potions
            elif p_inv.potion_type == [0, 0, 100, 0]: # blue
                net_blue_ml += (100 * p_inv.quantity)
                net_blue_pot += p_inv.quantity # add total number of green potions

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml - %d" % (net_green_ml)))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = num_green_potions + %d" % (net_green_pot)))

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml - %d" % (net_blue_ml)))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = num_blue_potions + %d" % (net_blue_pot)))

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml - %d" % (net_red_ml)))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = num_red_potions + %d" % (net_red_pot)))


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
        new_G_pot = green_ml_available // 100 # or however much mL per potion
        g_plan = {
                "potion_type": [0, 100, 0, 0],
                "quantity": new_G_pot,
            }

        blue_ml_available = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).first()[0]
        new_B_pot = blue_ml_available // 100 
        b_plan = {
                "potion_type": [0, 0, 100, 0],
                "quantity": new_B_pot,
            }

        red_ml_available = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).first()[0]
        new_R_pot = red_ml_available // 100
        r_plan = {
                "potion_type": [100, 0, 0, 0],
                "quantity": new_R_pot,
            }
        
    bot_plan = []
    if new_G_pot > 0:
        bot_plan.append(g_plan)
    if new_B_pot > 0:
        bot_plan.append(b_plan)
    if new_R_pot > 0:
        bot_plan.append(r_plan)
    return bot_plan

if __name__ == "__main__":
    print(get_bottle_plan())