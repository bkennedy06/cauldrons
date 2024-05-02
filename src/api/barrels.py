import sqlalchemy
from sqlalchemy.exc import IntegrityError
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    total_cost = 0 # price calculation
    greenMl = 0
    blueMl = 0
    redMl = 0 # Barrel type is always 1 instead of 100
    for barrel in barrels_delivered: # ml calculation, prolly have to update for multi colored barrels
        if barrel.potion_type == [0, 1, 0, 0]: # green
            greenMl += (barrel.ml_per_barrel * barrel.quantity) #ml per barrel
        elif barrel.potion_type == [1, 0, 0, 0]: # red
            redMl += (barrel.ml_per_barrel * barrel.quantity)
        elif barrel.potion_type == [0, 0, 1, 0]: # blue
            blueMl += (barrel.ml_per_barrel * barrel.quantity)
        total_cost += (barrel.price * barrel.quantity) # price per barrel
    
    with db.engine.begin() as connection: # update storage depending on potion
        try:
            if greenMl > 0:
                connection.execute(sqlalchemy.text("""INSERT INTO ledger (potion_type, gold_change, description) VALUES (:pot_type, :price, 'Green barrel purchased')"""),
                                   {'pot_type' : "[0, 1, 0, 0]", 'price' : (0 - total_cost)})
                connection.execute(sqlalchemy.text("""INSERT INTO liquid_ledger (g_ml, description) VALUES (:gml, 'Green barrel purchased')"""),
                                   {'gml' : greenMl})
            if redMl > 0:
                connection.execute(sqlalchemy.text("""INSERT INTO ledger (potion_type, gold_change, description) VALUES (:pot_type, :rml, :price, 'Red barrel purchased')"""),
                                   {'pot_type' : "[1, 0, 0, 0]", 'price' : (0 - total_cost)})
                connection.execute(sqlalchemy.text("""INSERT INTO liquid_ledger (r_ml, description) VALUES (:rml, 'Red barrel purchased')"""),
                                   {'rml' : redMl})
            if blueMl > 0:
                connection.execute(sqlalchemy.text("""INSERT INTO ledger (potion_type, gold_change, description) VALUES (:pot_type, :bml, :price, 'Blue barrel purchased')"""),
                                   {'pot_type' : "[0, 0, 1, 0]",  'price' : (0 - total_cost)})
                connection.execute(sqlalchemy.text("""INSERT INTO liquid_ledger (b_ml, description) VALUES (:bml, 'Blue barrel purchased')"""),
                                   {'bml' : blueMl})
        except IntegrityError as e:
            return "OK"
        
    return "OK"

# Gets called once a day
@router.post("/plan") # SHould buy multiple barrels at one go
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog) # [Barrel (type, sku, ml_per_barrel, potion type, price and quantity)]
                            # list of barrels
    with db.engine.begin() as connection:
        purch_power = connection.execute(sqlalchemy.text("SELECT SUM(gold_change) AS balance FROM ledger")).first()[0]
        num_green_ml = connection.execute(sqlalchemy.text("SELECT SUM(g_ml) AS ml FROM liquid_ledger")).first()[0]
        num_red_ml = connection.execute(sqlalchemy.text("SELECT SUM(r_ml) AS ml FROM liquid_ledger")).first()[0]
        num_blue_ml = connection.execute(sqlalchemy.text("SELECT SUM(b_ml) AS ml FROM liquid_ledger")).first()[0]

    if num_blue_ml is None:
        num_blue_ml = 0
    if num_red_ml is None:
        num_red_ml = 0
    if num_green_ml is None:
        num_green_ml = 0

    purchases = optimize_purchases(purch_power, [num_red_ml, num_green_ml, num_blue_ml, 0], wholesale_catalog)
    green_pur = {
            "sku": purchases[1][0],
            "quantity": purchases[1][1],
        }
    blue_pur = {
            "sku": purchases[2][0],
            "quantity": purchases[2][1],
        }
    red_pur = {
            "sku": purchases[0][0],
            "quantity": purchases[0][1],
        }
      
    pur_plan = [] # Should check if barrel is available in wholesale_catalogue, and dont buy if not enough gold
    if green_pur and purchases[1][1] != 0:
        pur_plan.append(green_pur)
    if blue_pur and purchases[2][1]:
        pur_plan.append(blue_pur)
    if red_pur and purchases[0][1]:
        pur_plan.append(red_pur)
    
    return pur_plan

def optimize_purchases(gold, current_stock, barrels: list[Barrel]):
    purchases = [(None, 0)] * 4

    best_barrels_per_type = [[] for _ in current_stock]
    for barrel in barrels:
        for i, type_present in enumerate(barrel.potion_type):
            if type_present:
                best_barrels_per_type[i].append(barrel)
    
    # Sort each list by cost per ml then price
    for i in range(len(best_barrels_per_type)):
        best_barrels_per_type[i].sort(key=lambda b: (b.price / b.ml_per_barrel, b.price))

    # buy on priority and available monies
    for index in sorted(range(len(current_stock)), key=lambda i: current_stock[i]):  # Sort by stock levels
        for barrel in best_barrels_per_type[index]:
            if barrel is None:
                continue

            unit_cost = barrel.price / barrel.ml_per_barrel
            if gold < unit_cost:  # Check if there's enough gold for one
                continue

            buyable_quant = min(int(gold / unit_cost), barrel.quantity)
            purchase_cost = buyable_quant * barrel.price

            purchases[index] = (barrel.sku, buyable_quant)

            # Update remaining gold
            gold -= purchase_cost

            # If out of gold, break early
            if gold <= 0:
                break
        if gold <= 0:
            break

    return purchases