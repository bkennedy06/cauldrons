import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit") # return all my stuff in my db
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        num_g_p = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).first()[0]
        num_r_p = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).first()[0]
        num_b_p = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).first()[0]
        gml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).first()[0]
        rml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).first()[0]
        bml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).first()[0]

        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first()[0]
    
    return {"number_of_potions": num_b_p + num_g_p + num_r_p, "ml_in_barrels": gml + rml + bml, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return {
        "potion_capacity": 50,
        "ml_capacity": 10000
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return "OK"
