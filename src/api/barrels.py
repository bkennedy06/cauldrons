import sqlalchemy
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
    for barrel in barrels_delivered: # ml calculation, prolly have to update for multi colored barrels
        greenMl += (barrel.ml_per_barrel * barrel.quantity) #ml per barrel
        total_cost += (barrel.price * barrel.quantity) # price per barrel

    with db.engine.begin() as connection:
        purchasedMl = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).first()[1] + greenMl
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :newGml"), newGml=purchasedMl)
        netGold = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).first()[2] - total_cost
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :netGold"), netGold=netGold)

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        num_green_potions = result.first()[0]
    if num_green_potions < 10:
        return [
        {
            "sku": "SMALL_GREEN_BARREL",
            "quantity": 1,
        }
        
    ]
    else: 
        return [] # no purchase

