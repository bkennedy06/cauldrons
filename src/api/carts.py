import sqlalchemy
from sqlalchemy.exc import IntegrityError
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import json
import re

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
    # Next and prev should be index of the returning array, first page is 0-4, next is 5-10, prev is 0-4, etc.
    # Search carts by name if applicable, also by potion sku if applicable.
    # Make function that returns a list of results, insert into return
    with db.engine.begin() as connection:
        if customer_name != "" and potion_sku != "": # Both searching
            result = connection.execute(sqlalchemy.text("SELECT potion_type, potion_quantity_change, cust_name, created_at, id FROM ledger WHERE potion_type = :type and cust_name = :name and description = 'Potions sold'"), {'type' : potion_sku, 'name' : customer_name})
        elif potion_sku == "" and customer_name != "": # search for customer name
            result = connection.execute(sqlalchemy.text("SELECT potion_type, potion_quantity_change, cust_name, created_at, id FROM ledger WHERE cust_name = :name and description = 'Potions sold'"), {'name' : customer_name})
        elif customer_name == "" and potion_sku != "": # search for potion_sku
            result = connection.execute(sqlalchemy.text("SELECT potion_type, potion_quantity_change, cust_name, created_at, id FROM ledger WHERE potion_type = :type and description = 'Potions sold'"), {'type' : potion_sku})
        else: # No search
            result = connection.execute(sqlalchemy.text("SELECT potion_type, potion_quantity_change, cust_name, created_at, id FROM ledger WHERE description = 'Potions sold'"))
    
    ret_result = []
    for order in result:
        pot_type, quant, name, time, id = order
        price = price_calc([pot_type], [quant]) * -1
        quant *= -1
        pot_name = namer(pot_type)
        # pot type is a list of potion types, need to differentiate
        res = {
                "line_item_id": id,
                "item_sku": f"{quant} of {pot_name}",
                "customer_name": name,
                "line_item_total": price,
                "timestamp": time,
            }
        ret_result.append(res)

    # Split array into chunks of 5 items each depending on next or prev values
    
    return {
        "previous": "",
        "next": "",
        "results": ret_result,
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
    with db.engine.begin() as connection: # orders = (id, type, quantitiy) type and quan are text arrays
        try: 
            cartID = connection.execute(sqlalchemy.text("INSERT INTO carts DEFAULT VALUES RETURNING id")).scalar()
            customer = new_cart.customer_name
            connection.execute(sqlalchemy.text("UPDATE carts SET customer_info = :cust WHERE id = :id"), {'cust' : customer, 'id' : cartID})
        except IntegrityError as e:
            return "OK"
        
    return {"cart_id": cartID}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}") # For selling more than 1 potions
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    potion_type = type_extracter(item_sku)
    print(potion_type)
    with db.engine.begin() as connection: # carts = (id, num_red_potions, num_green_potions, nblue)
        types = json.loads((connection.execute(sqlalchemy.text("SELECT type FROM carts WHERE id = %d" % (cart_id)))).scalar())
        quantities = json.loads((connection.execute(sqlalchemy.text("SELECT quantity FROM carts WHERE id = %d" % (cart_id)))).scalar())
        if potion_type in types: # Potion type already in cart
            quantities[types.index(potion_type)] = cart_item.quantity # Set quantity, probably not used
        else: # Potion type not in cart
            types.append(potion_type)
            quantities.append(cart_item.quantity) # Should be the same index

        connection.execute(sqlalchemy.text("UPDATE carts SET type = :types WHERE id = :id"), {'types': str(types), 'id' : cart_id})
        connection.execute(sqlalchemy.text("UPDATE carts SET quantity = :quan WHERE id = :id"), {'quan': str(quantities), 'id' : cart_id})
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout): # potions bought and gold paid should be based on car_id
    """ """
    with db.engine.begin() as connection:
        types = json.loads(connection.execute(sqlalchemy.text("SELECT type FROM carts WHERE id = %d" % (cart_id))).scalar()) # potions in cart with ID
        quantities = json.loads(connection.execute(sqlalchemy.text("SELECT quantity FROM carts WHERE id = %d" % (cart_id))).scalar())
        cust_name = connection.execute(sqlalchemy.text("SELECT customer_info FROM carts WHERE id = %d" % (cart_id))).scalar()
        shmoney = price_calc(types, quantities)
        #connection.execute(sqlalchemy.text("INSERT INTO ledger (gold_change, description) VALUES (:gold, 'Potion profit')"), {'gold' : shmoney})
        # gold should be positive
        i = 0
        for type in types: # remove potions from inv
            gold = connection.execute(sqlalchemy.text("SELECT price FROM potions WHERE type = :ptype"), {'ptype' : str(type)}).scalar() * quantities[i]
            connection.execute(sqlalchemy.text("INSERT INTO ledger (potion_type, potion_quantity_change, description, gold_change, cust_name) VALUES (:pot_type, :quantity, 'Potions sold', :gold, :name)"),
                                {'quantity' : 0 - quantities[i], 'pot_type' : str(type), 'gold' : gold, 'name' : cust_name})
            i += 1  # Potions should be negative

    return {"total_potions_bought": sum(quantities), "total_gold_paid": shmoney}

def type_extracter(item_sku):
    if item_sku == "Red_Potion":
        return [100, 0, 0 ,0]
    elif item_sku == "Green_Potion":
        return [0, 100, 0, 0]
    elif item_sku == "Blue_Potion":
        return [0, 0, 100, 0]
    else: # Custom potion
        return json.loads((re.search(r'\[(.*?)\]', item_sku)).group(0))

def price_calc(types, quantities):
    with db.engine.begin() as connection:
        shmoney = 0
        i = 0
        for type in types:
            price = connection.execute(sqlalchemy.text("SELECT price FROM potions WHERE type = :ptype"), {'ptype' : str(type)}).scalar()
            shmoney += (price * quantities[i])
            i += 1
    return shmoney

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
  