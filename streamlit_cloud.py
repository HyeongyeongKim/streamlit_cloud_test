import streamlit as st
st.title("Hello!")
st.write("I am Hyeongyeong Kim.")
st.write("What is your name?")
name = st.text_input("Write your name here")

if name:
    st.write(f"Hello, {name}!")
    st.write("Nice to meet you!")