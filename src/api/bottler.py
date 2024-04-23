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
                if 100 in p_inv.potion_type:
                    price = 50 # Standard potions
                else: price = 75 # custom potions
                red_ml += (p_inv.potion_type[0] * p_inv.quantity)
                green_ml += (p_inv.potion_type[1] * p_inv.quantity)
                blue_ml += (p_inv.potion_type[2] * p_inv.quantity) # should calculate total used

                curr_pot_type = str(p_inv.potion_type)
                in_potions = connection.execute(sqlalchemy.text("SELECT EXISTS (SELECT 1 FROM potions WHERE type = :pot_type)"), {'pot_type': curr_pot_type}).scalar()
                
                if in_potions: # Already in potions
                    connection.execute(sqlalchemy.text("UPDATE potions SET quantity = quantity + :quantity WHERE type = :pot_type"), {'quantity' : p_inv.quantity, 'pot_type' : curr_pot_type})
                else: # insert new value
                    connection.execute(sqlalchemy.text("INSERT INTO potions (type, quantity, price) VALUES (:pot_type, :quantity, :price)"), {'pot_type' : curr_pot_type, 'quantity' : p_inv.quantity, 'price' : price})

                # update quantity and row
                # multiply quantity by type's array              

            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml - %d" % (green_ml)))
        
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml - %d" % (blue_ml)))
            
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml - %d" % (red_ml)))
            
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
        green_ml_available = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).first()[0]

        blue_ml_available = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).first()[0]
        
        red_ml_available = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).first()[0]
        supplies = [red_ml_available, green_ml_available, blue_ml_available, 0] # Placeholder for dark

    
    return package(supplies)

def package(supplies):
    packages = []

    #At least one custom potion
    if sum(supplies) >= 100:
        mixed_package = [0] * len(supplies)
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

        package = [0] * len(supplies)
        total = 0
        
        for i in range(len(supplies)):
            if total < 100:
                max_take = min(supplies[i], 100 - total)
                package[i] = max_take
                supplies[i] -= max_take
                total += max_take

        packages.append(package)

    packages = {}
    for package in packages:
        key = tuple(package)
        if key in packages:
            packages[key]['quantity'] += 1
        else:
            packages[key] = {
                "potion_type": list(key),
                "quantity": 1
            }

    return list(packages.values())


if __name__ == "__main__":
    print(get_bottle_plan())