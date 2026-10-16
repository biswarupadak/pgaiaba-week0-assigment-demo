"""LangChain tools the Order Agent may call."""

from langchain_core.tools import tool

from . import database


@tool
def fetch_order_details(order_id: str) -> str:
    """
    Fetch all order details for a given order_id from the Kartify database.
    Use this tool whenever the customer's query requires order-specific information.
    Returns a formatted string of order details, or an error message if not found.
    """
    if not database.is_valid_order_id(order_id):
        return (f"Invalid order ID format: '{order_id}'. "
                "Expected format: O followed by digits (e.g. O40327).")
    try:
        df = database.get_order(order_id)
    except Exception as e:
        return f"Database error while fetching order {order_id}: {e}"
    if df.empty:
        return f"No order found with ID {order_id}."
    return df.to_string(index=False)


TOOLS = [fetch_order_details]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}
