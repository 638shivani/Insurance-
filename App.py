import streamlit as st

st.title("Insurance Claim Assistant 💡")

query = st.text_input("Enter your insurance question:")

if query:
    st.write("You asked:", query)
    st.write("Answer: This is a demo response (we will connect AI next 🚀)")
