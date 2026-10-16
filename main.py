"""Command-line chat with the Kartify Order Query Chatbot.

Usage:
    python main.py                       # prompts for customer and order ID
    python main.py --customer C1011 --order O48601 --debug
"""

import argparse

from kartify_chatbot import ChatSession
from kartify_chatbot import database


def choose_order(cust_id: str) -> str | None:
    orders = database.get_customer_orders(cust_id)
    if orders.empty:
        print(f"No orders found for Customer ID: {cust_id}")
        return None
    print(orders.to_string(index=False), end="\n\n")
    while True:
        order_id = input("Enter Order ID: ").strip()
        if order_id in set(orders["order_id"]):
            return order_id
        print("That order does not belong to this customer. Please pick one from the list.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Kartify Order Query Chatbot")
    parser.add_argument("--customer", help="Customer ID, e.g. C1011")
    parser.add_argument("--order", help="Order ID, e.g. O48601")
    parser.add_argument("--debug", action="store_true", help="print each node's state update")
    args = parser.parse_args()

    cust_id = (args.customer or input("Enter Customer ID: ")).strip()
    if args.order:
        if not database.order_belongs_to_customer(args.order, cust_id):
            parser.error(f"Order {args.order} does not belong to customer {cust_id}.")
        order_id = args.order.strip()
    else:
        order_id = choose_order(cust_id)
        if order_id is None:
            return

    session = ChatSession(cust_id, order_id, debug=args.debug)
    print("\nAsk about your order (type 'quit' to leave).")
    while not session.ended:
        query = input("User: ").strip()
        if not query:
            continue
        if query.lower() in {"quit", "exit"}:
            break
        print(f"Assistant: {session.ask(query).reply}")


if __name__ == "__main__":
    main()
