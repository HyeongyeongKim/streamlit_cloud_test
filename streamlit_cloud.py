import streamlit as st
st.title("안녕하세요!")
st.write("저는 김현경입니다")
st.write("이름이 무엇인가요?")
name = st.text_input("이름을 입력하세요")

if name:
    st.write(f"안녕하세요, {name}!")
    st.write("만나서 반갑습니다!")