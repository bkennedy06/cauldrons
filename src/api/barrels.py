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
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml + %d" % (greenMl)))
            if redMl > 0:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml + %d" % (redMl)))
            if blueMl > 0:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml + %d" % (blueMl)))

            connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - %d" % (total_cost))) # Subtract costs
        except IntegrityError as e:
            return "OK"
        
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog) # [Barrel (type, sku, ml_per_barrel, potion type, price and quantity)]
                            # list of barrels
    with db.engine.begin() as connection:
        num_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).first()[0]
        num_red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).first()[0]
        num_blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).first()[0]
        purch_power = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first()[0]
    green_pur = {
            "sku": "SMALL_GREEN_BARREL",
            "quantity": 1,
        }
    blue_pur = {
            "sku": "SMALL_BLUE_BARREL",
            "quantity": 1,
        }
    red_pur = {
            "sku": "SMALL_RED_BARREL",
            "quantity": 1,
        }
    
    g_cost = 0
    r_cost = 0
    b_cost = 0
    for b in wholesale_catalog:
        if b.sku == "SMALL_GREEN_BARREL":
            g_cost = b.price
        elif b.sku == "SMALL_RED_BARREL":
            r_cost = b.price
        elif b.sku == "SMALL_BLUE_BARREL":
            b_cost = b.price
            
    pur_plan = [] # Should check if barrel is available in wholesale_catalogue, and dont buy if not enough gold
    if num_green_ml < 150 and any("SMALL_GREEN_BARREL" in barrel.sku for barrel in wholesale_catalog) and purch_power >= g_cost:
        pur_plan.append(green_pur)
        purch_power -= g_cost
    if num_red_ml < 150 and any("SMALL_RED_BARREL" in barrel.sku for barrel in wholesale_catalog) and purch_power >= r_cost: 
        pur_plan.append(red_pur)
        purch_power -= r_cost
    if num_blue_ml < 150 and any("SMALL_BLUE_BARREL" in barrel.sku for barrel in wholesale_catalog) and purch_power >= b_cost:
        pur_plan.append(blue_pur)
        purch_power -= b_cost

    return pur_plan
