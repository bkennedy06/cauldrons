import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """
    
    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK" 

@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    with db.engine.begin() as connection: # orders = (id, num_red_potions, num_green_potions, nblue)
        cartID =connection.execute(sqlalchemy.text("INSERT INTO orders DEFAULT VALUES RETURNING id"))
        
    return {"cart_id": cartID}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}") # For selling more than 1 potions
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection: # orders = (id, num_red_potions, num_green_potions, nblue)
        connection.execute(sqlalchemy.text("SELECT * FROM orders WHERE id = %d" % (cart_id)))
        if item_sku == "GREEN_POTION_0":
            connection.execute(sqlalchemy.text("UPDATE orders SET num_green_potions = %d WHERE id = %d" % (cart_item.quantity, cart_id)))
        elif item_sku == "RED_POTION_0":
            connection.execute(sqlalchemy.text("UPDATE orders SET num_red_potions = %d WHERE id = %d" % (cart_item.quantity, cart_id)))
        elif item_sku == "BLUE_POTION_0":
            connection.execute(sqlalchemy.text("UPDATE orders SET num_blue_potions = %d WHERE id = %d" % (cart_item.quantity, cart_id)))
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout): # potions bought and gold paid should be based on car_id
    """ """
    with db.engine.begin() as connection:
        cur_gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first()[0]
        potions = connection.execute(sqlalchemy.text("SELECT * FROM orders WHERE id = %d" % (cart_id))).first() # potions sold

        totPot = 0
        if potions[1] > 0: # [1] = red [2] = green [3] = blue
            totPot += potions[1]
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = num_red_potions - %d" % (potions[1])))
        if potions[2] > 0:
            totPot += potions[2]
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = num_green_potions - %d" % (potions[2])))
        if potions[3] > 0:
            totPot += potions[3]
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = num_blue_potions - %d" % (potions[3])))

        net_gold = cur_gold + (totPot * 40) # Standard price across the board
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = %d" % (net_gold)))


    return {"total_potions_bought": totPot, "total_gold_paid": totPot * 40}
