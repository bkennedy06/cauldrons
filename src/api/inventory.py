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
        gold = connection.execute(sqlalchemy.text("""SELECT SUM(gold_change) as gold FROM ledger""")).first()[0]
        
        potions = connection.execute(sqlalchemy.text("SELECT SUM(potion_quantity_change) AS total_quantity FROM ledger")).scalar()
        if potions is None:
            potions = 0
        rml = connection.execute(sqlalchemy.text("SELECT SUM(r_ml) AS rml FROM liquid_ledger")).scalar()
        gml = connection.execute(sqlalchemy.text("SELECT SUM(g_ml) AS gml FROM liquid_ledger")).scalar()
        bml = connection.execute(sqlalchemy.text("SELECT SUM(b_ml) AS bml FROM liquid_ledger")).scalar()
        
        
    return {"number_of_potions": potions, "ml_in_barrels": rml + gml + bml, "gold": gold}

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
