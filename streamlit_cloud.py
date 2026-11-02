from datetime import date

import streamlit as st

st.set_page_config(page_title="오늘의 투두리스트", page_icon="📝", layout="wide")

if "todos" not in st.session_state:
    st.session_state.todos = []
if "next_todo_id" not in st.session_state:
    st.session_state.next_todo_id = 0

for todo in st.session_state.todos:
    checkbox_key = f"todo_{todo['id']}"
    if checkbox_key in st.session_state:
        todo["done"] = st.session_state[checkbox_key]

with st.sidebar:
    st.header("📝 오늘의 계획")
    with st.form("todo_form", clear_on_submit=True):
        task = st.text_input("새로운 할 일", placeholder="예: 산책하기")
        category = st.selectbox("분류", ["개인", "공부", "일"])
        priority = st.select_slider("우선순위", ["낮음", "보통", "높음"], value="보통")
        due_date = st.date_input("마감일", value=date.today())
        submitted = st.form_submit_button("할 일 추가", use_container_width=True)

if submitted:
    if task.strip():
        st.session_state.todos.append(
            {
                "id": st.session_state.next_todo_id,
                "title": task.strip(),
                "category": category,
                "priority": priority,
                "due_date": due_date,
                "done": False,
            }
        )
        st.session_state.next_todo_id += 1
    else:
        st.warning("할 일을 입력해 주세요.")

completed_count = sum(todo["done"] for todo in st.session_state.todos)
with st.sidebar:
    st.divider()
    view = st.radio("목록 보기", ["전체", "미완료", "완료"])
    st.metric("완료한 할 일", f"{completed_count} / {len(st.session_state.todos)}")
    if st.button("완료 항목 지우기", use_container_width=True):
        for todo in st.session_state.todos:
            if todo["done"]:
                st.session_state.pop(f"todo_{todo['id']}", None)
        st.session_state.todos = [
            todo for todo in st.session_state.todos if not todo["done"]
        ]
        st.rerun()

st.title("🌷 오늘의 투두리스트")
if st.session_state.todos:
    st.progress(completed_count / len(st.session_state.todos), text="오늘의 진행률")

visible_todos = [
    todo
    for todo in st.session_state.todos
    if view == "전체"
    or (view == "미완료" and not todo["done"])
    or (view == "완료" and todo["done"])
]

if visible_todos:
    for todo in visible_todos:
        with st.container(border=True):
            st.checkbox(todo["title"], key=f"todo_{todo['id']}")
            st.caption(
                f"{todo['category']} · 우선순위 {todo['priority']} · "
                f"마감일 {todo['due_date'].strftime('%m월 %d일')}"
            )
else:
    st.info("표시할 할 일이 없어요. 사이드바에서 할 일을 추가해 보세요!")
