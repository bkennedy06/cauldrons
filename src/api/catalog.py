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
    catalog = []
    with db.engine.begin() as connection: # Should return specific columns
        top_6 = wut_2_sell()
        print(top_6)
        for potion in top_6: # (type, quantity)
            price = connection.execute(sqlalchemy.text("SELECT price FROM potions WHERE type = :pot_t"), {'pot_t' : potion[0]}).first()[0]
            print(potion[0])
            arr_type = json.loads(potion[0])
            print((type(arr_type)))
            sale = {
                "sku": skuer(potion[0]),
                "name": namer(potion[0]),
                "quantity": potion[1],
                "price": price,
                "potion_type": arr_type,
            }
            catalog.append(sale)

    return catalog

def skuer(potion):
    type = json.loads(potion)
    if type[0] == 100:
        return "Red_Potion"
    elif type[1] == 100:
        return "Green_Potion"
    elif type[2] == 100:
        return "Blue_Potion"
    else:
        return "Custom_Potion_" + potion

def namer(potion):
    type = json.loads(potion)
    if type[0] == 100:
        return "Red Potion"
    elif type[1] == 100:
        return "Green Potion"
    elif type[2] == 100:
        return "Blue Potion"
    else:
        return "Custom Potion: " + potion
    
def wut_2_sell(): # Return an array of 6 tuples of type and quantity
    selling = []
    with db.engine.begin() as connection:
        potion_types = connection.execute(sqlalchemy.text("SELECT type FROM potions"))
        for pot in potion_types:
                pot_type = str(pot[0])
                quantity = connection.execute(sqlalchemy.text("SELECT SUM(potion_quantity_change) AS pots FROM ledger WHERE potion_type = :pot_t"), {'pot_t' : pot_type}).scalar()
                if quantity is None:
                    quantity = 0
                if quantity != 0:
                    selling.append((pot_type, quantity))
    
    sorted_sellin = sorted(selling, key=lambda x: x[1], reverse=True)

    if len(sorted_sellin) > 6:
        return sorted_sellin[:6] # Can only have 6 different types, sell what weve got the most of
    else:
        return sorted_sellin