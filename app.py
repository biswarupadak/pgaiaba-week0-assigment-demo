"""Streamlit web app for the Kartify Order Query Chatbot.

Run locally:  streamlit run app.py
On Streamlit Cloud, set OPENAI_API_KEY (and optionally OPENAI_BASE_URL) as secrets,
or upload config.json alongside this file.
"""

import os

import streamlit as st

from kartify_chatbot import ChatSession
from kartify_chatbot import database

st.set_page_config(page_title="Kartify Order Assistant", page_icon="📦")
st.title("📦 Kartify Order Assistant")

# Streamlit secrets → environment (config.json is used as a fallback by load_credentials).
for key in ("OPENAI_API_KEY", "OPENAI_BASE_URL"):
    try:
        if key in st.secrets and not os.getenv(key):
            os.environ[key] = st.secrets[key]
    except FileNotFoundError:
        pass  # no secrets.toml locally


def reset_chat():
    st.session_state.pop("session", None)
    st.session_state.messages = []


# ---- Sidebar: pick customer and order ----
with st.sidebar:
    st.header("Customer")
    cust_id = st.text_input("Customer ID", placeholder="e.g. C1011").strip()
    order_id = None
    if cust_id:
        orders = database.get_customer_orders(cust_id)
        if orders.empty:
            st.warning(f"No orders found for {cust_id}.")
        else:
            labels = {f"{r.order_id} — {r.product_description}": r.order_id
                      for r in orders.itertuples()}
            order_id = labels[st.selectbox("Order", list(labels))]
    st.button("New conversation", on_click=reset_chat)

if not order_id:
    st.info("Enter your Customer ID and choose an order to start chatting.")
    st.stop()

# A new customer/order pair starts a fresh session.
session = st.session_state.get("session")
if session is None or (session.cust_id, session.order_id) != (cust_id, order_id):
    session = st.session_state.session = ChatSession(cust_id, order_id)
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if session.ended:
    st.info("This conversation has ended. Click **New conversation** to start again.")
elif query := st.chat_input(f"Ask about order {order_id}"):
    st.session_state.messages.append({"role": "user", "content": query})
    st.chat_message("user").write(query)
    with st.spinner("Checking your order..."):
        result = session.ask(query)
    st.session_state.messages.append({"role": "assistant", "content": result.reply})
    st.chat_message("assistant").write(result.reply)
    if result.ended:
        st.rerun()
