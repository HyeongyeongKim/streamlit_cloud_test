from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from html import escape
import calendar
import json
import streamlit as st
from garden_api import GardenClient, APIError
from planner import (BANDS, STATUS, MOODS, REACTIONS, BASE, PALETTES, FONTS,
                     clean_theme, ink_on, contrast, clock, schedule_values,
                     task_band, task_sort, timing)

st.set_page_config(page_title='오늘의 정원 | 나의 속도로', layout='wide')
TODAY = datetime.now(ZoneInfo('Asia/Seoul')).date()


def theme_css(theme):
    t = clean_theme(theme)
    font = FONTS[t['font']][1]
    st.markdown(f'''<style>
    @import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Nanum+Gothic:wght@400;700&family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
    :root {{ --paper:{t['background']}; --ink:{t['text']}; --card:{t['card']}; --soft:{t['calendar']}; --accent:{t['accent']}; }}
    .stApp, [data-testid="stHeader"] {{ background:var(--paper); color:var(--ink); }}
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label, .stApp input,
    .stApp textarea, .stApp button, .stApp select {{ font-family:'{font}',sans-serif; }}
    .stApp h1 {{ font-size:2.6rem; font-weight:500; letter-spacing:-.055em; padding-bottom:.7rem; }}
    .stApp h2 {{ font-size:1.45rem; font-weight:500; letter-spacing:-.035em; }}
    .stApp h3 {{ font-size:1.15rem; font-weight:500; letter-spacing:-.02em; }}
    .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3 {{ color:var(--ink); }}
    [data-testid="stCaptionContainer"] p {{ color:var(--ink); opacity:.76; }}
    [data-testid="stSidebar"] {{ background:var(--card); border-right:1px solid color-mix(in srgb,var(--ink) 12%,transparent); }}
    [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stForm"], [data-testid="stExpander"] {{
      background:var(--card); border-color:color-mix(in srgb,var(--ink) 16%,transparent); border-radius:16px; box-shadow:none; }}
    [data-testid="stForm"] {{ padding:1.3rem; }}
    .stApp button {{ border-radius:9px; box-shadow:none; min-height:42px; }}
    [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"] {{ background:var(--card); color:var(--ink); border-color:color-mix(in srgb,var(--ink) 23%,transparent); }}
    [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {{ background:var(--accent); border-color:var(--accent); color:{ink_on(t['accent'])}; }}
    [data-testid="stBaseButton-primary"] p, [data-testid="stBaseButton-primaryFormSubmit"] p {{ color:{ink_on(t['accent'])}; }}
    .stApp input, .stApp textarea, [data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"] {{ background:var(--paper); color:var(--ink); }}
    .stApp input::placeholder, .stApp textarea::placeholder {{ color:var(--ink); opacity:.55; }}
    [data-testid="stAlert"] {{ background:var(--soft); color:var(--ink); border-radius:12px; }}
    .block-container {{ max-width:1050px; padding-top:2.8rem; padding-bottom:5rem; }}
    .eyebrow {{ font-size:.72rem; letter-spacing:.18em; margin:0 0 .8rem; opacity:.65; }}
    .day-band {{ padding:1rem 0 .6rem; border-top:1px solid color-mix(in srgb,var(--ink) 17%,transparent); margin-top:1rem; }}
    .day-band strong {{ font-size:1.2rem; font-weight:500; }}
    .day-band span {{ float:right; font-size:.8rem; opacity:.65; padding-top:.3rem; }}
    .quiet-note {{ background:var(--soft); padding:1.1rem 1.3rem; border-radius:12px; line-height:1.8; margin:.5rem 0 1rem; }}
    .task-title {{ font-weight:500; font-size:1.08rem; margin-bottom:.3rem; overflow-wrap:anywhere; }}
    .task-meta {{ font-size:.8rem; opacity:.72; margin-bottom:.7rem; }}
    .calendar-grid {{ display:grid; grid-template-columns:repeat(7,minmax(0,1fr)); gap:5px; margin:1rem 0; }}
    .calendar-cell {{ min-height:76px; padding:8px; background:var(--paper); border-radius:8px; font-size:.85rem; }}
    .calendar-cell.selected {{ outline:2px solid var(--accent); background:var(--soft); }}
    .calendar-cell small {{ display:block; font-size:.65rem; opacity:.75; margin-top:6px; }}
    .calendar-head {{ text-align:center; font-size:.75rem; opacity:.65; }}
    @media(max-width:640px) {{ .block-container {{ padding:1.2rem .8rem 3rem; }} .stApp h1 {{ font-size:2rem; }}
      [data-testid="stForm"] {{ padding:.85rem; }} .calendar-cell {{ min-height:65px; padding:5px; }} }}
    </style>''', unsafe_allow_html=True)


def heading(kicker, title, subtitle=''):
    st.markdown(f'<div class="eyebrow">{escape(kicker)}</div>', unsafe_allow_html=True)
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def clear_login():
    client = st.session_state.get('client')
    if client:
        client.close()
    st.session_state.clear()


def change(action, notice='저장했어요.', **values):
    try:
        st.session_state.client.change(action, **values)
        if action == 'task.add':
            st.session_state.reset_new_task = True
        st.session_state.notice = notice
        st.rerun()
    except APIError as exc:
        st.error(str(exc))


def auth_screen():
    theme_css(BASE)
    heading('ONEUL GARDEN / DAILY PLANNER', '오늘의 정원', '나의 속도로 계획하고, 서로의 응원으로 이어가는 하루.')
    st.markdown('<div class="quiet-note">오전, 오후, 밤. 아직 시간을 정하지 않은 일까지.<br>계획은 가볍게, 기록은 있는 그대로 남겨요.</div>', unsafe_allow_html=True)
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
    st.caption('기록은 기본적으로 나에게만 보여요. 공유하고 싶은 일정만 직접 선택할 수 있어요.')
    st.caption('브라우저를 새로고침하면 다시 로그인해야 할 수 있지만 저장된 기록은 유지됩니다.')


def reactions(row, kind, data, feed=False):
    key = ('feedTaskReactions' if feed else 'taskReactions') if kind == 'task' else ('feedDiaryReactions' if feed else 'diaryReactions')
    items = [r for r in data[key] if r[kind + '_id'] == row['id']]
    if feed:
        cols = st.columns(2)
        for i, (code, label) in enumerate(REACTIONS.items()):
            count = sum(r['emoji'] == code for r in items)
            mine = any(r.get('user_id') == data['me'].get('id') and r['emoji'] == code for r in items)
            if cols[i % 2].button(f'{label} · {count}', key=f'react_{kind}_{row["id"]}_{ord(code[0])}', type='primary' if mine else 'secondary', use_container_width=True):
                change('reaction', notice='반응을 반영했어요.', kind=kind, id=row['id'], emoji=code)
        st.caption('한 기록에 하나의 반응을 남겨요. 같은 반응을 다시 누르면 취소돼요.')
    elif items:
        st.caption(' · '.join(f'{label} {sum(r["emoji"] == code for r in items)}' for code, label in REACTIONS.items() if any(r['emoji'] == code for r in items)))


def schedule_fields(prefix, task=None):
    task = task or {}
    band = st.selectbox('시간대', list(BANDS), index=list(BANDS).index(task_band(task)), format_func=BANDS.get, key=prefix+'_band')
    st.caption('시각은 비워 두어도 좋아요. 입력하면 오전(0–12시) · 오후(12–18시) · 밤(18–24시)으로 정리돼요.')
    left, right = st.columns(2)
    start = left.time_input('시작 시각 (선택)', value=clock(task.get('planned_start')), key=prefix+'_start', step=300)
    end = right.time_input('종료 시각 (선택)', value=clock(task.get('planned_end')), key=prefix+'_end', step=300)
    fixed = st.checkbox('시간이 정해진 약속', value=bool(task.get('is_fixed')), key=prefix+'_fixed', help='오늘 줄이기로 한꺼번에 옮길 수 없어요.')
    return band, start, end, fixed


def task_card(task, data, extended):
    with st.container(border=True):
        meta = timing(task)+' / '+STATUS.get(task['status'], '할 예정')+(' / 약속' if task.get('is_fixed') else '')+(' / 공유 중' if task['visibility']=='shared' else ' / 나만 보기')
        st.markdown(f'<div class="task-title">{escape(task["title"])}</div><div class="task-meta">{escape(meta)}</div>', unsafe_allow_html=True)
        if task.get('actual_start'):
            st.caption('실제 기록 · '+task['actual_start']+('–'+task['actual_end'] if task.get('actual_end') else ''))
        if task.get('note'):
            st.write(task['note'])
        reactions(task, 'task', data)
        if task['status'] not in ('done','skipped','missed'):
            left, right = st.columns(2)
            if left.button('완료했어요', key='done_'+task['id'], use_container_width=True):
                change('task.update', id=task['id'], status='done', notice='오늘의 실천을 남겼어요.')
            if right.button('조금 진행했어요', key='partial_'+task['id'], disabled=not extended or task['status']=='partial', use_container_width=True):
                change('task.update', id=task['id'], status='partial', notice='조금 이어간 것도 기록이에요.')
        with st.expander('일정 수정 · 실제 기록'):
            with st.form('task_'+task['id']):
                title = st.text_input('할 일', value=task['title'], max_chars=160)
                target = st.date_input('날짜', value=date.fromisoformat(task['date']))
                choices = list(STATUS) if extended else ['todo','done','missed']
                status = st.selectbox('진행 상태', choices, index=choices.index(task['status']) if task['status'] in choices else 0, format_func=STATUS.get)
                if extended:
                    band, start, end, fixed = schedule_fields('edit_'+task['id'], task)
                    st.markdown('**실제로 한 시간**')
                    a, b = st.columns(2)
                    actual_start = a.time_input('실제 시작 (선택)', value=clock(task.get('actual_start')), step=300)
                    actual_end = b.time_input('실제 종료 (선택)', value=clock(task.get('actual_end')), step=300)
                    note = st.text_area('짧은 기록', value=task.get('note',''), max_chars=1000, placeholder='조금 해 본 일, 바뀐 계획. 적고 싶을 때만 남겨요.')
                shared = st.checkbox('다른 회원에게 공유', value=task['visibility']=='shared')
                share_time = st.checkbox('공유할 때 시간도 보여주기', value=bool(task.get('share_time')), disabled=not extended)
                if st.form_submit_button('변경 저장', type='primary'):
                    try:
                        if not title.strip():
                            raise ValueError('할 일을 입력해 주세요.')
                        extra = schedule_values(band, start, end, fixed, actual_start, actual_end) if extended else {}
                        if extended:
                            extra.update(note=note, shareTime=share_time)
                        change('task.update', id=task['id'], title=title, date=target.isoformat(), status=status, visibility='shared' if shared else 'private', **extra)
                    except ValueError as exc:
                        st.warning(str(exc))
            if not task.get('is_fixed') and task['status']=='todo':
                if st.button('다음 날로 옮기기', key='next_'+task['id']):
                    change('task.update', id=task['id'], date=(date.fromisoformat(task['date'])+timedelta(days=1)).isoformat(), notice='다음 날에 이어갈 수 있도록 옮겼어요.')
            confirmed = st.checkbox('이 일정을 삭제할게요', key='confirm_t_'+task['id'])
            if st.button('일정 삭제', key='delete_t_'+task['id'], disabled=not confirmed):
                change('task.delete', id=task['id'], notice='일정을 삭제했어요.')


def month_calendar(data, selected):
    cells = [f'<div class="calendar-head">{d}</div>' for d in ['월','화','수','목','금','토','일']]
    for week in calendar.Calendar().monthdatescalendar(selected.year, selected.month):
        for day in week:
            if day.month != selected.month:
                cells.append('<div></div>')
                continue
            tasks = [t for t in data['tasks'] if t['date']==day.isoformat()]
            diaries = [d for d in data['diaries'] if d['date']==day.isoformat()]
            count = sum(t['status'] in ('done','partial') for t in tasks)
            summary = (f'일정 {len(tasks)}<br>실천 {count}' if tasks else '')+('<br>일기' if diaries else '')
            cells.append(f'<div class="calendar-cell {"selected" if day==selected else ""}">{day.day}<small>{summary}</small></div>')
    st.markdown('<div class="calendar-grid">'+''.join(cells)+'</div>', unsafe_allow_html=True)


def today_screen(data, extended):
    if st.session_state.pop('reset_new_task', False):
        for key in list(st.session_state):
            if key.startswith('new_task_') or key in ('new_band','new_start','new_end','new_fixed'):
                del st.session_state[key]
    heading('MY DAY', '오늘도, 나의 속도로', '다 채우지 않아도 괜찮은 하루. 필요한 만큼만 계획해요.')
    selected = st.date_input('기록할 날짜', value=TODAY, key='selected_date')
    when = selected.isoformat()
    tasks = [t for t in data['tasks'] if t['date']==when]
    if not extended:
        st.info('기존 일정은 그대로 사용할 수 있어요. 시간대·실제 시간·조금 진행 기능은 저장 서버 업데이트 후 열립니다.')
    with st.expander('새 일정 추가', expanded=not tasks):
        with st.form('new_task'):
            title = st.text_input('새로운 할 일', placeholder='오늘 마음에 두고 있는 일', max_chars=160, key='new_task_title')
            if extended:
                band, start, end, fixed = schedule_fields('new')
            shared = st.checkbox('이 일정을 다른 회원에게 공유', key='new_task_shared')
            share_time = st.checkbox('공유할 때 시간도 보여주기', disabled=not extended, key='new_task_share_time')
            if st.form_submit_button('일정 추가', type='primary', use_container_width=True):
                try:
                    if not title.strip():
                        raise ValueError('할 일을 입력해 주세요.')
                    extra = schedule_values(band, start, end, fixed) if extended else {}
                    if extended:
                        extra['shareTime'] = share_time
                    change('task.add', title=title, date=when, visibility='shared' if shared else 'private', **extra)
                except ValueError as exc:
                    st.warning(str(exc))
    with st.expander('오늘 줄이기'):
        st.write('남은 계획이 버겁다면, 지금 필요한 일만 남겨요.')
        eligible = [t for t in tasks if t['status']=='todo' and not t.get('is_fixed') and not t.get('actual_start')]
        if eligible and extended:
            with st.form('lighten'):
                lookup = {t['id']:t['title'] for t in eligible}
                ids = st.multiselect('다른 날로 옮길 일', list(lookup), format_func=lookup.get)
                target = st.date_input('이어갈 날짜', value=selected+timedelta(days=1))
                if st.form_submit_button('선택한 일정 옮기기'):
                    if not ids:
                        st.warning('옮길 일정을 선택해 주세요.')
                    elif target==selected:
                        st.warning('다른 날짜를 선택해 주세요.')
                    else:
                        change('task.reschedule', ids=ids, fromDate=when, date=target.isoformat(), notice='선택한 일정만 옮겼어요. 지금의 속도로 이어가요.')
            st.caption('시간이 정해진 약속과 이미 실천한 기록은 그대로 두어요.')
        else:
            st.caption('옮길 수 있는 유동 일정이 없어요.' if extended else '저장 서버 업데이트 후 사용할 수 있어요.')
    if not tasks:
        st.markdown('<div class="quiet-note">아직 비어 있는 하루예요.<br>작은 일 하나부터 남겨 볼까요?</div>', unsafe_allow_html=True)
    for band in ['morning','afternoon','night','anytime']:
        group = sorted([t for t in tasks if task_band(t)==band], key=task_sort)
        descriptions = {'morning':'하루를 여는 시간','afternoon':'이어가는 시간','night':'마무리하는 시간','anytime':'시간을 정하지 않은 일'}
        st.markdown(f'<div class="day-band"><strong>{BANDS[band]}</strong><span>{descriptions[band]}</span></div>', unsafe_allow_html=True)
        if not group:
            st.caption('비워 두어도 좋아요.')
        for task in group:
            task_card(task, data, extended)
    with st.expander('이번 달 기록'):
        st.caption('날짜는 화면 위의 날짜 선택에서 바꿀 수 있어요.')
        month_calendar(data, selected)


def diary_card(row, data, feed=False):
    with st.container(border=True):
        st.subheader(f'{row["date"]} · {MOODS.get(row["mood"], "보통")}')
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
            if comment['diary_id']==row['id']:
                st.write(f'{comment["name"]}: {comment["body"]}')
        if feed:
            with st.form('comment_'+row['id'], clear_on_submit=True):
                body = st.text_input('전하고 싶은 말', max_chars=1000)
                if st.form_submit_button('댓글 남기기'):
                    if body.strip():
                        change('comment.add', id=row['id'], body=body)
                    else:
                        st.warning('댓글 내용을 입력해 주세요.')
        else:
            with st.expander('일기 수정 · 공개 설정'):
                with st.form('diary_edit_'+row['id']):
                    body = st.text_area('내용', value=row['body'], max_chars=10000)
                    mood = st.selectbox('감정', list(MOODS), index=list(MOODS).index(row['mood']), format_func=MOODS.get)
                    shared = st.checkbox('다른 회원에게 공유', value=row['visibility']=='shared')
                    if st.form_submit_button('수정 저장'):
                        if body.strip():
                            change('diary.update', id=row['id'], body=body, mood=mood, visibility='shared' if shared else 'private')
                        else:
                            st.warning('일기 내용을 입력해 주세요.')
                confirm = st.checkbox('이 일기를 삭제합니다', key='confirm_d_'+row['id'])
                if st.button('일기 삭제', key='delete_d_'+row['id'], disabled=not confirm):
                    change('diary.delete', id=row['id'])


def diary_screen(data):
    heading('DAILY NOTES', '하루의 메모', '계획에 담기지 않은 마음도, 남기고 싶을 때만.')
    with st.expander('일기 쓰기', expanded=not data['diaries']):
        with st.form('new_diary', clear_on_submit=True):
            day = st.date_input('일기 날짜', value=TODAY)
            mood = st.selectbox('오늘의 감정', list(MOODS), index=2, format_func=MOODS.get)
            body = st.text_area('오늘의 이야기', max_chars=10000)
            photo = st.file_uploader('사진 한 장 (5MB 이하)', type=['jpg','jpeg','png','webp','gif'])
            shared = st.checkbox('다른 회원에게 공유하고 응원받기')
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


def habit_screen(data):
    heading('SMALL ROUTINES', '작게, 꾸준히', '매일 완벽할 필요 없이. 다시 해 본 날을 남겨요.')
    day = st.date_input('습관 기록 날짜', value=TODAY)
    names, ids = ['월','화','수','목','금','토','일'], [1,2,3,4,5,6,0]
    with st.expander('반복 습관 추가'):
        with st.form('new_habit', clear_on_submit=True):
            title = st.text_input('습관 이름', max_chars=100)
            days = st.multiselect('반복 요일', names, default=names)
            if st.form_submit_button('습관 추가'):
                if not title.strip() or not days:
                    st.warning('습관 이름과 반복 요일을 선택해 주세요.')
                else:
                    change('habit.add', title=title, days=[ids[names.index(d)] for d in days], emoji='')
    due = [h for h in data['habits'] if str((day.weekday()+1)%7) in h['days'].split(',')]
    checked = {c['habit_id'] for c in data['checks'] if c['date']==day.isoformat()}
    for habit in due:
        value = st.checkbox(habit['title'], value=habit['id'] in checked, key='habit_'+habit['id']+day.isoformat())
        if value != (habit['id'] in checked):
            change('habit.check', id=habit['id'], date=day.isoformat(), checked=value)
    if due and all(h['id'] in checked for h in due):
        st.success('오늘의 실천을 모두 남겼어요. 이제 편하게 쉬어 가요.')
    elif not due:
        st.info('이날 예정된 습관이 없어요.')
    with st.expander('습관 관리'):
        for habit in data['habits']:
            st.write(habit['title'])
            confirm = st.checkbox('기록과 함께 삭제', key='confirm_h_'+habit['id'])
            if st.button('습관 삭제', key='delete_h_'+habit['id'], disabled=not confirm):
                change('habit.delete', id=habit['id'])


def feed_screen(data):
    heading('TOGETHER', '서로의 하루', '각자의 속도로 이어가는 기록에, 짧은 응원을 남겨요.')
    st.caption('회원이 공유한 최근 기록이에요. 내 비공개 일정은 다른 사람에게 보이지 않아요.')
    for task in data['sharedTasks']:
        with st.container(border=True):
            st.caption(f'{task["owner_name"]} · {task["date"]}')
            st.subheader(task['title'])
            st.caption(STATUS.get(task['status'],'할 예정')+' · '+timing(task, shared=True))
            if task.get('share_time') and task.get('actual_start'):
                st.caption('실제 기록 · '+task['actual_start']+('–'+task['actual_end'] if task.get('actual_end') else ''))
            if task.get('note'):
                st.write(task['note'])
            reactions(task, 'task', data, True)
    for row in data['sharedDiaries']:
        diary_card(row, data, True)
    if not data['sharedTasks'] and not data['sharedDiaries']:
        st.info('아직 공유된 기록이 없어요. 일정에서 공유를 선택하면 서로의 하루에 표시돼요.')


def appearance_screen(saved_theme):
    heading('YOUR SPACE', '내 취향의 화면', '매트한 색과 편안한 글꼴로, 오래 머물고 싶은 공간을 만들어요.')
    preset = st.selectbox('추천 색 조합', list(PALETTES))
    swatch = PALETTES[preset]
    st.markdown('<div style="display:flex;gap:8px;margin:8px 0 16px">'+''.join(f'<span style="background:{swatch[k]};border:1px solid #8886;border-radius:50%;width:32px;height:32px;display:inline-block" title="{k}"></span>' for k in ['background','card','calendar','accent','text'])+'</div>', unsafe_allow_html=True)
    if st.button('이 색 조합 적용'):
        change('theme.save', theme={**swatch,'font':saved_theme['font']})
    with st.form('theme'):
        st.subheader('직접 고르기')
        t = {}
        for key, label in [('background','배경'),('text','글씨'),('card','카드'),('calendar','부드러운 강조 영역'),('accent','버튼과 강조색')]:
            t[key] = st.color_picker(label, saved_theme[key], key=f'theme_{key}_{saved_theme[key]}')
        t['font'] = st.selectbox('글꼴', list(FONTS), index=list(FONTS).index(saved_theme['font']), format_func=lambda x:FONTS[x][0], key='font_'+saved_theme['font'])
        st.caption('노토 산스는 단정하게, 나눔고딕은 또렷하게, 고운돋움은 부드럽게 읽혀요.')
        if st.form_submit_button('미리 보기'):
            st.session_state.theme_preview = t
        if st.form_submit_button('내 화면 저장', type='primary'):
            if min(contrast(t['text'], t[k]) for k in ('background','card','calendar')) < 3:
                st.warning('글씨와 배경이 비슷해서 읽기 어려워요. 글씨를 더 밝게 또는 어둡게 골라 주세요.')
            else:
                st.session_state.pop('theme_preview', None)
                change('theme.save', theme=t)
    if st.session_state.get('theme_preview'):
        t = clean_theme(st.session_state.theme_preview)
        st.markdown(f'<div style="padding:24px;border:1px solid {t["accent"]};border-radius:14px;background:{t["background"]};color:{t["text"]};font-family:\'{FONTS[t["font"]][1]}\',sans-serif"><div style="font-size:22px">오늘도, 나의 속도로</div><div style="margin-top:16px;padding:16px;background:{t["card"]};border-radius:10px">오후 · 책 10쪽 읽기<br><small>조금 이어간 것도 기록이에요.</small></div></div>', unsafe_allow_html=True)
        st.caption('미리 보기예요. 저장 버튼을 눌러야 다음 로그인에도 적용돼요.')
    if st.button('기본 화면으로 되돌리기'):
        st.session_state.pop('theme_preview', None)
        change('theme.save', theme=BASE)


if 'client' not in st.session_state:
    st.session_state.client = GardenClient()
if not st.session_state.get('logged_in'):
    auth_screen()
    st.stop()
try:
    data = st.session_state.client.data()
except APIError as exc:
    if exc.status==401:
        clear_login()
        st.rerun()
    st.error(str(exc))
    if st.button('다시 연결'):
        st.rerun()
    st.stop()
try:
    saved_theme = clean_theme(json.loads(data['me']['theme']))
except (ValueError, TypeError):
    saved_theme = BASE.copy()
theme_css(saved_theme)
extended = 'schedule-v1' in data.get('capabilities', [])
with st.sidebar:
    st.markdown('<div class="eyebrow">DAILY PLANNER</div>', unsafe_allow_html=True)
    st.title('오늘의 정원')
    st.caption(f'{data["me"]["name"]}님의 하루')
    page = st.radio('메뉴', ['오늘 · 일정','내 기록','함께','일기','습관','화면 설정','계정'], label_visibility='collapsed')
    st.divider()
    st.caption('계획은 바뀌어도, 남긴 하루는 그대로예요.')
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

if page=='오늘 · 일정':
    today_screen(data, extended)
elif page=='내 기록':
    heading('MY RECORDS', '남겨 온 하루', '연속 기록보다, 다시 돌아온 하루를 기억해요.')
    selected = st.date_input('돌아볼 날짜', value=TODAY)
    month_calendar(data, selected)
    tasks = [t for t in data['tasks'] if t['date']==selected.isoformat()]
    diaries = [d for d in data['diaries'] if d['date']==selected.isoformat()]
    for task in sorted(tasks, key=task_sort):
        task_card(task, data, extended)
    for row in diaries:
        diary_card(row, data)
    if not tasks and not diaries:
        st.info('이날은 남긴 기록이 없어요. 빈 날은 그대로 두어도 좋아요.')
elif page=='일기':
    diary_screen(data)
elif page=='습관':
    habit_screen(data)
elif page=='함께':
    feed_screen(data)
elif page=='화면 설정':
    appearance_screen(saved_theme)
else:
    heading('ACCOUNT', '계정 관리')
    st.write('탈퇴하면 일정, 일기, 사진, 습관과 반응이 삭제됩니다.')
    with st.form('delete_account'):
        password = st.text_input('현재 비밀번호', type='password', max_chars=128)
        confirm = st.text_input('확인을 위해 탈퇴를 입력해 주세요')
        if st.form_submit_button('회원탈퇴'):
            if confirm!='탈퇴':
                st.warning('탈퇴를 정확하게 입력해 주세요.')
            else:
                try:
                    st.session_state.client.change('account.delete', password=password)
                    clear_login()
                    st.rerun()
                except APIError as exc:
                    st.error(str(exc))
