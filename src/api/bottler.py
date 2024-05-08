import sqlalchemy
from sqlalchemy.exc import IntegrityError
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

        supplies = [red_ml_available, green_ml_available, blue_ml_available, 0] # Placeholder for dark

    potions = package(supplies)

    
    if len(potions > 50): # Restricted on 50 potions at a time
        potions = potions[:49]
    return 

def package(supplies): # Just populate db with custom potions, query them to see which we can make
    packages = []
    print(supplies)
    #At least one custom potion
    if sum(supplies) >= 100:
        mixed_package = [0] * 4
        total = 0

        for i in range(len(supplies)):
            if total < 100 and supplies[i] > 0:
                
                max_take = min(supplies[i], 100 - total)
                if max_take == 100 and total == 0 and sum(supplies) - supplies[i] >= 100:
                    # If possible, take less than 100 to allow mixing
                    max_take -= min(25, max_take)
                mixed_package[i] = max_take
                supplies[i] -= max_take
                total += max_take
                if total >= 100:
                    break

        if total == 100:
            packages.append(mixed_package)

    # Continue with previous logic to fill up packages using available supplies
    while sum(supplies) >= 100:
        single_package_made = False
        for i in range(len(supplies)):
            if supplies[i] >= 100:
                package = [0] * len(supplies)
                package[i] = 100
                supplies[i] -= 100
                packages.append(package)
                single_package_made = True
                break

        if single_package_made:
            continue

        package = [0] * 4
        total = 0
        
        for i in range(len(supplies)):
            if total < 100:
                max_take = min(supplies[i], 100 - total)
                package[i] = max_take
                supplies[i] -= max_take
                total += max_take

        packages.append(package)

    ret_list = []
    while len(packages) > 0:
        potion = packages[0]
        quantity = packages.count(potion)
        packages = [element for element in packages if element != potion]
        ret_list.append({
            "potion_type": potion,
            "quantity": quantity
        })


    return ret_list

#[
#    {
#        "potion_type": [r, g, b, d],
#        "quantity": "integer"
#    }
#]


if __name__ == "__main__":
    print(get_bottle_plan())