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
        connection.execute(sqlalchemy.text("TRUNCATE TABLE ledger RESTART IDENTITY"))
        connection.execute(sqlalchemy.text("INSERT INTO ledger (description, gold_change) VALUES ('Reset', 100)"))

        connection.execute(sqlalchemy.text("TRUNCATE TABLE liquid_ledger RESTART IDENTITY"))
        connection.execute(sqlalchemy.text("INSERT INTO liquid_ledger DEFAULT VALUES"))
        
        connection.execute(sqlalchemy.text("TRUNCATE TABLE carts RESTART IDENTITY"))
        connection.execute(sqlalchemy.text("TRUNCATE TABLE capacity RESTART IDENTITY"))
        connection.execute(sqlalchemy.text("INSERT INTO capacity DEFAULT VALUES"))
        # delete order records, reset id counter
    return "OK"

