import sqlalchemy
from sqlalchemy.exc import IntegrityError
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
from src.api import inventory
import json

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
        try:
            red_ml = 0
            green_ml = 0
            blue_ml = 0
            for p_inv in potions_delivered: # if p_type in potions, add or decrement
                red_ml = (p_inv.potion_type[0] * p_inv.quantity)
                green_ml = (p_inv.potion_type[1] * p_inv.quantity)
                blue_ml = (p_inv.potion_type[2] * p_inv.quantity) # should calculate total used

                curr_pot_type = str(p_inv.potion_type)
                
                # maybe try to sync id from ledger to liquid ledger
                # Add potions, decrement ml's * quantity
                connection.execute(sqlalchemy.text("INSERT INTO ledger (potion_type, potion_quantity_change, description) VALUES (:pot_type, :quantity, 'Potions bottled')"), {'pot_type' : curr_pot_type, 'quantity' : p_inv.quantity})
                connection.execute(sqlalchemy.text("INSERT INTO liquid_ledger (r_ml, g_ml, b_ml, description) VALUES (:r_ml, :g_ml, :b_ml, 'Potions bottled')"),
                                    {'r_ml' : (0 - red_ml), 'g_ml' : (0 - green_ml), 'b_ml' : (0 - blue_ml)})           
            
        except IntegrityError as e:
            return "OK"

    return "OK"

@router.post("/plan") # request potions made
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    
    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    with db.engine.begin() as connection:
        green_ml_available = connection.execute(sqlalchemy.text("SELECT SUM(g_ml) AS ml FROM liquid_ledger")).first()[0]
        red_ml_available = connection.execute(sqlalchemy.text("SELECT SUM(r_ml) AS ml FROM liquid_ledger")).first()[0]
        blue_ml_available = connection.execute(sqlalchemy.text("SELECT SUM(b_ml) AS ml FROM liquid_ledger")).first()[0]

        potion_options = connection.execute(sqlalchemy.text("SELECT type FROM potions"))
        pot_cap = connection.execute(sqlalchemy.text("SELECT pot_cap FROM capacity")).first()[0]
        inv = inventory.get_inventory()
        total_potions = inv["number_of_potions"]
        pot_cap = pot_cap - total_potions
        supplies = [red_ml_available, green_ml_available, blue_ml_available, 0] # Placeholder for dark

    if pot_cap == 0:
        return []

    pot_ops = []
    for ptype in potion_options:
        pot_ops.append(json.loads(ptype[0]))
    potions = package(supplies, pot_ops, pot_cap)


    return potions

def package(mls, potion_options, max_potions):
    results = []
    total_packages = 0

    for config in potion_options:
        max_possible = float('inf')  
        
        for i in range(len(mls)):
            if config[i] > 0:
                max_possible = min(max_possible, mls[i] // config[i])
        
        packages_to_make = min(max_possible, max_potions - total_packages)

        # Update ml's based on potions made
        for i in range(len(mls)):
            mls[i] -= packages_to_make * config[i]

        # Keep track of total potions made 
        total_packages += packages_to_make

        if packages_to_make > 0:
            results.append({
                "potion_type": config,
                "quantity": packages_to_make
            })

        if total_packages >= max_potions:
            break

    return results

#[
#    {
#        "potion_type": [r, g, b, d],
#        "quantity": "integer"
#    }
#]


if __name__ == "__main__":
    print(get_bottle_plan())