from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import calendar
import json
import re
import streamlit as st
from garden_api import GardenClient, APIError

st.set_page_config(page_title='오늘의 정원', page_icon='🌷', layout='wide')
TODAY = datetime.now(ZoneInfo('Asia/Seoul')).date()
MOODS = {'great': '🥰 아주 좋아', 'good': '😊 좋아', 'okay': '😌 보통', 'low': '😔 조금 우울', 'hard': '😢 힘들어'}
STATUS = {'todo': '🟡 할 예정', 'done': '✅ 했어요', 'missed': '⭕ 못했어요'}
FONTS = {'pretendard': 'Noto Sans KR', 'noto': 'Noto Sans KR', 'nanum': 'Nanum Gothic', 'gowun': 'Gowun Dodum'}
BASE = dict(background='#F7F6F0', text='#263A32', card='#FFFFFF', calendar='#E9F2EC', accent='#579778', font='noto')
PALETTES = {'초록 정원': BASE, '복숭아': dict(background='#FFF6EE', text='#3E3433', card='#FFFFFF', calendar='#FDEBDD', accent='#C86B4F', font='gowun'), '라벤더': dict(background='#F4F0FA', text='#493A50', card='#FFFFFF', calendar='#EBE6F7', accent='#8061AF', font='nanum'), '파란 하늘': dict(background='#EDF5FA', text='#33455A', card='#FFFFFF', calendar='#E5F0F9', accent='#437CA9', font='noto')}


def theme_css(theme):
    t = BASE.copy()
    for key in BASE:
        value = theme.get(key, '')
        if key != 'font' and re.fullmatch(r'#[0-9a-fA-F]{6}', str(value)):
            t[key] = value
    font = FONTS.get(theme.get('font'), FONTS['noto'])
    st.markdown(f'''<style>
    @import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Nanum+Gothic&family=Noto+Sans+KR:wght@400;600;700&display=swap');
    .stApp, [data-testid="stHeader"] {{background:{t['background']};color:{t['text']};}}
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label, .stApp button {{font-family:'{font}',sans-serif;}}
    [data-testid="stSidebar"], [data-testid="stVerticalBlockBorderWrapper"] {{background:{t['card']};}}
    [data-testid="stBaseButton-primary"] {{background:{t['accent']};border-color:{t['accent']};color:white;}}
    [data-testid="stDateInput"] {{background:{t['calendar']};padding:8px;border-radius:12px;}}
    .block-container {{max-width:1120px;padding-top:2rem;}}
    @media(max-width:640px) {{.block-container {{padding:1rem;}} h1 {{font-size:1.8rem!important;}}}}
    </style>''', unsafe_allow_html=True)


def clear_login():
    client = st.session_state.get('client')
    if client:
        client.close()
    st.session_state.clear()


def change(action, **values):
    try:
        st.session_state.client.change(action, **values)
        st.session_state.notice = '저장했어요.'
        st.rerun()
    except APIError as exc:
        st.error(str(exc))


def auth_screen():
    theme_css(BASE)
    st.title('🌷 오늘의 정원')
    st.subheader('할 일도, 마음도, 작은 습관도 한곳에.')
    st.write('날짜별 할 일을 정리하고 오늘의 마음을 기록해 보세요. 공유하고 싶은 기록만 함께 나눌 수 있어요.')
    mode = st.radio('시작하기', ['로그인', '회원가입'], horizontal=True)
    with st.form('auth'):
        name = st.text_input('닉네임', max_chars=30) if mode == '회원가입' else ''
        email = st.text_input('이메일', max_chars=254)
        password = st.text_input('비밀번호', type='password', max_chars=128, help='가입 시 12자 이상 입력해 주세요.')
        confirm = st.text_input('비밀번호 확인', type='password', max_chars=128) if mode == '회원가입' else ''
        submit = st.form_submit_button(mode, type='primary', use_container_width=True)
    if submit:
        try:
            st.session_state.client.auth('register' if mode == '회원가입' else 'login', email=email, password=password, name=name, passwordConfirm=confirm)
            st.session_state.logged_in = True
            st.rerun()
        except APIError as exc:
            st.error(str(exc))
    st.caption('ChatGPT 계정 없이 이용할 수 있습니다. 새로고침하면 다시 로그인해야 할 수 있지만 저장한 기록은 유지됩니다.')


def reactions(row, kind, data, feed=False):
    items = data[('feedTaskReactions' if feed else 'taskReactions') if kind == 'task' else ('feedDiaryReactions' if feed else 'diaryReactions')]
    fk = kind + '_id'
    counts = {emoji: sum(r[fk] == row['id'] and r['emoji'] == emoji for r in items) for emoji in ['💚', '👏', '✨', '🫶']}
    if feed:
        for col, (emoji, count) in zip(st.columns(4), counts.items()):
            if col.button(f'{emoji} {count}', key=f'react_{kind}_{row["id"]}_{emoji}', help='같은 반응을 다시 누르면 취소됩니다.'):
                change('reaction', kind=kind, id=row['id'], emoji=emoji)
    elif any(counts.values()):
        st.caption('  ·  '.join(f'{e} {n}' for e, n in counts.items() if n))


def diary_card(row, data, feed=False):
    with st.container(border=True):
        st.subheader(f'{row["date"]} · {MOODS.get(row["mood"], "😌")}')
        if feed:
            st.caption(row['owner_name'])
        st.write(row['body'])
        if row.get('photo_key'):
            try:
                st.image(st.session_state.client.photo(row['photo_key']), width='stretch')
            except APIError as exc:
                st.warning(str(exc))
        reactions(row, 'diary', data, feed)
        for comment in data['feedComments' if feed else 'comments']:
            if comment['diary_id'] == row['id']:
                st.write(f'{comment["name"]}: {comment["body"]}')
        if feed:
            with st.form('comment_' + row['id'], clear_on_submit=True):
                body = st.text_input('따뜻한 한마디', max_chars=1000)
                if st.form_submit_button('댓글 남기기'):
                    change('comment.add', id=row['id'], body=body)
        else:
            with st.expander('일기 수정 · 공개 설정'):
                with st.form('edit_' + row['id']):
                    body = st.text_area('내용', value=row['body'], max_chars=10000)
                    mood = st.selectbox('감정', list(MOODS), index=list(MOODS).index(row['mood']), format_func=MOODS.get)
                    shared = st.checkbox('다른 회원에게 공유', value=row['visibility'] == 'shared')
                    if st.form_submit_button('수정 저장'):
                        change('diary.update', id=row['id'], body=body, mood=mood, visibility='shared' if shared else 'private')
                confirm = st.checkbox('이 일기를 삭제합니다', key='confirm_' + row['id'])
                if st.button('일기 삭제', key='delete_' + row['id'], disabled=not confirm):
                    change('diary.delete', id=row['id'])


if 'client' not in st.session_state:
    st.session_state.client = GardenClient()
if not st.session_state.get('logged_in'):
    auth_screen()
    st.stop()
try:
    data = st.session_state.client.data()
except APIError as exc:
    if exc.status == 401:
        clear_login()
        st.rerun()
    st.error(str(exc))
    if st.button('다시 연결'):
        st.rerun()
    st.stop()
try:
    saved_theme = json.loads(data['me']['theme'])
except (ValueError, TypeError):
    saved_theme = BASE
if not isinstance(saved_theme, dict):
    saved_theme = BASE
saved_theme = {**BASE, **saved_theme}
theme_css(saved_theme)
with st.sidebar:
    st.title('🌷 오늘의 정원')
    st.write(f'{data["me"]["name"]}님의 하루')
    page = st.radio('메뉴', ['오늘 · 달력', '일기', '습관', '함께', '꾸미기', '계정'])
    st.caption('일정은 날짜별 할 일, 습관은 반복해서 쌓는 기록이에요.')
    if st.button('로그아웃', use_container_width=True):
        try:
            st.session_state.client.auth('logout')
        except APIError as exc:
            st.error(str(exc))
        else:
            clear_login()
            st.rerun()
if st.session_state.get('notice'):
    st.success(st.session_state.pop('notice'))

if page == '오늘 · 달력':
    st.title('오늘도, 나의 속도로 🌿')
    selected = st.date_input('기록할 날짜', value=TODAY, key='selected_date')
    when = selected.isoformat()
    with st.expander('월간 기록 한눈에 보기', expanded=True):
        st.caption('✅ 완료 · ⭕ 못함 · 🟡 예정 · 📔 일기 — 날짜 변경은 위 달력에서 선택하세요.')
        for col, label in zip(st.columns(7), ['월', '화', '수', '목', '금', '토', '일']):
            col.caption(label)
        for week in calendar.Calendar().monthdatescalendar(selected.year, selected.month):
            for col, day in zip(st.columns(7), week):
                if day.month != selected.month:
                    col.caption(' ')
                    continue
                tasks = [t for t in data['tasks'] if t['date'] == day.isoformat()]
                marks = ''.join(x for status, x in [('done', '✅'), ('missed', '⭕'), ('todo', '🟡')] if any(t['status'] == status for t in tasks))
                if any(d['date'] == day.isoformat() for d in data['diaries']):
                    marks += '📔'
                col.write(f'{day.day}\n{marks}')
    tasks = [t for t in data['tasks'] if t['date'] == when]
    if tasks:
        done = sum(t['status'] == 'done' for t in tasks)
        st.progress(done / len(tasks), text=f'{done}/{len(tasks)} 완료')
    with st.form('new_task', clear_on_submit=True):
        title = st.text_input('새로운 할 일', placeholder='예: 저녁 산책 20분', max_chars=160)
        shared = st.checkbox('이 할 일을 다른 회원에게 공유')
        if st.form_submit_button('할 일 추가', type='primary'):
            change('task.add', title=title, date=when, visibility='shared' if shared else 'private')
    for task in tasks:
        with st.container(border=True):
            st.subheader(task['title'])
            st.caption(STATUS[task['status']] + (' · 공유 중' if task['visibility'] == 'shared' else ' · 나만 보기'))
            reactions(task, 'task', data)
            with st.form('task_' + task['id']):
                status = st.radio('진행 상태', list(STATUS), index=list(STATUS).index(task['status']), format_func=STATUS.get, horizontal=True)
                target = st.date_input('옮길 날짜', value=selected)
                shared = st.checkbox('다른 회원에게 공유', value=task['visibility'] == 'shared')
                if st.form_submit_button('변경 저장'):
                    change('task.update', id=task['id'], date=target.isoformat(), status=status, visibility='shared' if shared else 'private')
            if st.button('다음 날로 미루기', key='next_' + task['id']):
                change('task.update', id=task['id'], date=(selected + timedelta(days=1)).isoformat(), status='todo')
            with st.expander('삭제'):
                if st.button('이 할 일 삭제', key='delete_' + task['id']):
                    change('task.delete', id=task['id'])
    if not tasks:
        st.info('아직 할 일이 없어요. 작은 일부터 하나 남겨 보세요.')
elif page == '일기':
    st.title('📔 마음을 남기는 시간')
    with st.form('new_diary', clear_on_submit=True):
        day = st.date_input('일기 날짜', value=TODAY)
        mood = st.selectbox('오늘의 감정', list(MOODS), format_func=MOODS.get)
        body = st.text_area('오늘의 이야기', max_chars=10000)
        photo = st.file_uploader('사진 한 장 (5MB 이하)', type=['jpg', 'jpeg', 'png', 'webp', 'gif'])
        shared = st.checkbox('다른 회원에게 공유하고 반응·댓글 받기')
        if st.form_submit_button('일기 저장', type='primary'):
            if not body.strip():
                st.warning('일기 내용을 입력해 주세요.')
            else:
                try:
                    key = st.session_state.client.upload(photo) if photo else ''
                    change('diary.add', date=day.isoformat(), mood=mood, body=body, photoKey=key, visibility='shared' if shared else 'private')
                except APIError as exc:
                    st.error(str(exc))
    for row in data['diaries']:
        diary_card(row, data)
elif page == '습관':
    st.title('🌱 조금씩 자라는 나')
    st.write('요일마다 반복할 행동을 정해 보세요. 하루의 할 일과 별도로 꾸준함을 기록합니다.')
    day = st.date_input('습관 기록 날짜', value=TODAY)
    names = ['월', '화', '수', '목', '금', '토', '일']
    ids = [1, 2, 3, 4, 5, 6, 0]
    with st.form('new_habit', clear_on_submit=True):
        title = st.text_input('습관 이름', max_chars=100)
        days = st.multiselect('반복 요일', names, default=names)
        if st.form_submit_button('습관 심기'):
            change('habit.add', title=title, days=[ids[names.index(d)] for d in days], emoji='🌱')
    due = [h for h in data['habits'] if str((day.weekday() + 1) % 7) in h['days'].split(',')]
    checked = {c['habit_id'] for c in data['checks'] if c['date'] == day.isoformat()}
    for habit in due:
        value = st.checkbox(habit['title'], value=habit['id'] in checked, key='habit_' + habit['id'] + day.isoformat())
        if value != (habit['id'] in checked):
            change('habit.check', id=habit['id'], date=day.isoformat(), checked=value)
    if due and all(h['id'] in checked for h in due):
        st.success('🌸 오늘의 정원이 활짝 피었어요! 약속한 습관을 모두 지켰어요.')
        celebration = 'celebrate_' + day.isoformat() + '_' + ','.join(sorted(checked))
        if not st.session_state.get(celebration):
            st.balloons()
            st.session_state[celebration] = True
    elif not due:
        st.info('이날 예정된 습관이 없어요.')
    with st.expander('습관 관리'):
        for habit in data['habits']:
            st.write(habit['title'])
            confirm = st.checkbox('기록과 함께 삭제', key='confirm_h_' + habit['id'])
            if st.button('습관 삭제', key='delete_h_' + habit['id'], disabled=not confirm):
                change('habit.delete', id=habit['id'])
elif page == '함께':
    st.title('💚 서로의 하루를 응원해요')
    st.caption('회원이 직접 공유한 최근 기록만 표시됩니다. 비공개 기록은 보이지 않아요.')
    for task in data['sharedTasks']:
        with st.container(border=True):
            st.write(task['title'])
            st.caption(f'{task["owner_name"]} · {task["date"]} · {STATUS[task["status"]]}')
            reactions(task, 'task', data, True)
    for row in data['sharedDiaries']:
        diary_card(row, data, True)
    if not data['sharedTasks'] and not data['sharedDiaries']:
        st.info('아직 공유된 기록이 없어요.')
elif page == '꾸미기':
    st.title('🎨 나만의 정원 꾸미기')
    preset = st.selectbox('추천 색 조합', list(PALETTES))
    if st.button('이 색 조합 적용'):
        change('theme.save', theme=PALETTES[preset])
    st.caption('색상 사각형을 눌러 고르세요. 색상 코드를 직접 입력할 필요가 없습니다.')
    with st.form('theme'):
        t = {}
        for key, label in [('background', '배경'), ('text', '글씨'), ('card', '카드'), ('calendar', '달력'), ('accent', '강조')]:
            t[key] = st.color_picker(label, saved_theme[key])
        t['font'] = st.selectbox('무료 글꼴', ['noto', 'nanum', 'gowun'], format_func=lambda x: {'noto': '노토 산스', 'nanum': '나눔고딕', 'gowun': '고운돋움'}[x])
        if st.form_submit_button('내 테마 저장', type='primary'):
            change('theme.save', theme=t)
else:
    st.title('계정 관리')
    st.write('탈퇴하면 일정, 일기, 사진, 습관과 반응이 삭제됩니다.')
    with st.form('delete_account'):
        password = st.text_input('현재 비밀번호', type='password', max_chars=128)
        confirm = st.text_input('확인을 위해 탈퇴를 입력해 주세요')
        if st.form_submit_button('회원탈퇴'):
            if confirm != '탈퇴':
                st.warning('탈퇴를 정확하게 입력해 주세요.')
            else:
                try:
                    st.session_state.client.change('account.delete', password=password)
                    clear_login()
                    st.rerun()
                except APIError as exc:
                    st.error(str(exc))
