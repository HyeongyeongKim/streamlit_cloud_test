from datetime import date

import streamlit as st

st.set_page_config(page_title="오늘의 투두리스트", page_icon="📝", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');
    html, body, [class*="css"], [data-testid="stSidebar"] {
        font-family: "Jua", "Malgun Gothic", sans-serif;
        color: #222222;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "todos" not in st.session_state:
    st.session_state.todos = []
if "next_todo_id" not in st.session_state:
    st.session_state.next_todo_id = 0
if "diary" not in st.session_state:
    st.session_state.diary = {}


def update_todo(todo_id: int) -> None:
    todo = next(todo for todo in st.session_state.todos if todo["id"] == todo_id)
    todo["done"] = st.session_state[f"todo_{todo_id}"]

with st.sidebar:
    st.title("🌷 나의 기록")
    page = st.radio("메뉴", ["홈", "일기"], horizontal=True)
    st.divider()
    st.caption(f"오늘은 {date.today().strftime('%Y년 %m월 %d일')}")

if page == "홈":
    st.title("🏠 오늘의 할 일")
    st.write("하나씩 체크하며 오늘을 채워봐요!")

    with st.form("todo_form", clear_on_submit=True):
        task = st.text_input("새로운 할 일", placeholder="예: 산책하기")
        left, right = st.columns(2)
        with left:
            category = st.selectbox("분류", ["개인", "공부", "일"])
        with right:
            priority = st.selectbox("우선순위", ["낮음", "보통", "높음"], index=1)
        due_date = st.date_input("마감일", value=date.today())
        submitted = st.form_submit_button("➕ 할 일 추가", use_container_width=True)

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
            st.rerun()
        else:
            st.warning("할 일을 입력해 주세요.")

    completed_count = sum(todo["done"] for todo in st.session_state.todos)
    total_count = len(st.session_state.todos)
    if total_count:
        st.progress(completed_count / total_count, text=f"진행률 {completed_count}/{total_count}")

    view = st.radio("할 일 보기", ["전체", "미완료", "완료"], horizontal=True)
    visible_todos = [
        todo
        for todo in st.session_state.todos
        if view == "전체"
        or (view == "미완료" and not todo["done"])
        or (view == "완료" and todo["done"])
    ]

    if visible_todos:
        if completed_count and st.button("완료한 할 일 지우기"):
            for todo in st.session_state.todos:
                if todo["done"]:
                    st.session_state.pop(f"todo_{todo['id']}", None)
            st.session_state.todos = [
                todo for todo in st.session_state.todos if not todo["done"]
            ]
            st.rerun()

        for todo in visible_todos:
            with st.container(border=True):
                checkbox_key = f"todo_{todo['id']}"
                if checkbox_key not in st.session_state:
                    st.session_state[checkbox_key] = todo["done"]
                st.checkbox(
                    todo["title"],
                    key=checkbox_key,
                    on_change=update_todo,
                    args=(todo["id"],),
                )
                st.caption(
                    f"{todo['category']} · 우선순위 {todo['priority']} · "
                    f"마감일 {todo['due_date'].strftime('%m월 %d일')}"
                )
    else:
        st.info("할 일을 추가해 보세요!" if not total_count else "표시할 할 일이 없어요.")

else:
    st.title("📔 오늘의 일기")
    st.write("오늘의 기분과 기억을 짧게 남겨보세요.")
    with st.form("diary_form"):
        diary_date = st.date_input("날짜", value=date.today(), key="diary_date")
        mood = st.selectbox(
            "오늘의 감정",
            ["😊 행복해요", "😌 편안해요", "😢 슬퍼요", "😡 화나요", "😴 피곤해요"],
        )
        note = st.text_area("오늘의 이야기", placeholder="오늘은 어떤 하루였나요?")
        save_diary = st.form_submit_button("💌 일기 저장", use_container_width=True)

    if save_diary:
        st.session_state.diary[diary_date.isoformat()] = {
            "mood": mood,
            "note": note.strip(),
        }
        st.success("일기를 저장했어요!")

    if st.session_state.diary:
        st.subheader("지난 일기")
        for saved_date, entry in sorted(st.session_state.diary.items(), reverse=True):
            with st.container(border=True):
                st.markdown(f"**{saved_date} · {entry['mood']}**")
                st.write(entry["note"] or "짧은 하루 기록")
    else:
        st.info("아직 쓴 일기가 없어요. 오늘의 기분을 기록해 보세요!")
