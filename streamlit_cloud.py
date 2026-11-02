import streamlit as st

st.set_page_config(page_title="오늘의 투두리스트", page_icon="📝")

if "todos" not in st.session_state:
    st.session_state.todos = []

st.title("📝 오늘의 투두리스트")

with st.form("todo_form", clear_on_submit=True):
    task = st.text_input("할 일", placeholder="예: 산책하기")
    submitted = st.form_submit_button("추가")

if submitted:
    if task.strip():
        st.session_state.todos.append(task.strip())
    else:
        st.warning("할 일을 입력해 주세요.")

if st.session_state.todos:
    for index, todo in enumerate(st.session_state.todos):
        st.checkbox(todo, key=f"todo_{index}")
else:
    st.caption("할 일을 추가해 보세요!")
