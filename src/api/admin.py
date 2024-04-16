import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection: # update storage depending on potions
        connection.execute(sqlalchemy.text("""
        UPDATE global_inventory SET
            num_green_ml = 0,
            num_green_potions = 0,
            num_blue_potions = 0,
            num_blue_ml = 0,
            num_red_ml = 0,
            num_red_potions = 0,
            gold = 100"""))
        connection.execute(sqlalchemy.text("DELETE FROM orders")) # delete order records, reset id counter
        connection.execute(sqlalchemy.text("ALTER SEQUENCE orders_id_seq RESTART WITH 1"))
    return "OK"

