"""Presentation and validation shared by the schedule UI and tests."""
from datetime import time
import re

BANDS = {'anytime': '오늘 중', 'morning': '오전', 'afternoon': '오후', 'night': '밤'}
STATUS = {'todo': '할 예정', 'partial': '조금 진행', 'done': '완료', 'skipped': '안 하기로 결정', 'missed': '쉬어 간 일'}
MOODS = {'great': '아주 좋아', 'good': '좋아', 'okay': '보통', 'low': '조금 가라앉아', 'hard': '힘들어'}
# Keep the existing API identifiers so past reactions remain visible.
REACTIONS = {'\U0001f49a': '응원해요', '\U0001f44f': '수고했어요', '\u2728': '나도 시작할게요', '\U0001faf6': '천천히 해도 좋아요'}


def clock(value):
    return time.fromisoformat(value) if value else None


def time_text(value):
    return value.strftime('%H:%M') if value else ''


def schedule_values(band, start, end, fixed=False, actual_start=None, actual_end=None):
    if band not in BANDS:
        raise ValueError('시간대를 선택해 주세요.')
    for first, last in [(start, end), (actual_start, actual_end)]:
        if last and not first:
            raise ValueError('종료 시각을 넣으려면 시작 시각도 입력해 주세요.')
        if first and last and last <= first:
            raise ValueError('종료 시각은 시작 시각보다 늦어야 해요. 자정을 넘는 일정은 날짜별로 나눠 주세요.')
    if fixed and not start:
        raise ValueError('시간이 정해진 약속에는 시작 시각을 입력해 주세요.')
    if start:
        band = 'morning' if start.hour < 12 else 'afternoon' if start.hour < 18 else 'night'
    return dict(timeBand=band, plannedStart=time_text(start), plannedEnd=time_text(end),
                actualStart=time_text(actual_start), actualEnd=time_text(actual_end), isFixed=fixed)


def task_band(task):
    return task.get('time_band') if task.get('time_band') in BANDS else 'anytime'


def task_sort(task):
    return (task.get('planned_start') or '99:99', task.get('created_at', 0), task['id'])


def timing(task, shared=False):
    if shared and not task.get('share_time'):
        return '시간 비공개'
    label = BANDS[task_band(task)]
    if task.get('planned_start'):
        label += ' · ' + task['planned_start']
        if task.get('planned_end'):
            label += '–' + task['planned_end']
    return label


FONTS = {'noto': ('노토 산스', 'Noto Sans KR'), 'nanum': ('나눔고딕', 'Nanum Gothic'), 'gowun': ('고운돋움', 'Gowun Dodum')}
BASE = dict(background='#F3F1EC', text='#343B38', card='#FAF9F6', calendar='#E7EAE3', accent='#526657', font='noto')
PALETTES = {
    '오트 · 세이지': BASE,
    '클레이 · 로즈': dict(background='#F4EEEA', text='#493B38', card='#FCF8F5', calendar='#ECE0DA', accent='#855D55', font='gowun'),
    '미스트 · 블루': dict(background='#EDF0F2', text='#343E49', card='#F8FAFB', calendar='#DFE6EB', accent='#526B80', font='noto'),
    '페이퍼 · 라일락': dict(background='#F0EEF3', text='#403B49', card='#FAF9FC', calendar='#E4DFEC', accent='#6D617F', font='nanum'),
    '차콜 · 샌드': dict(background='#242724', text='#E8E7DF', card='#2E332F', calendar='#3C443E', accent='#C0C9B9', font='noto'),
}


def clean_theme(theme):
    clean = BASE.copy()
    if not isinstance(theme, dict):
        return clean
    for key in BASE:
        value = theme.get(key)
        if key != 'font' and isinstance(value, str) and re.fullmatch(r'#[0-9a-fA-F]{6}', value):
            clean[key] = value
    clean['font'] = theme.get('font') if theme.get('font') in FONTS else 'noto'
    return clean


def luminance(color):
    rgb = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    rgb = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb]
    return sum(c * weight for c, weight in zip(rgb, [.2126, .7152, .0722]))


def contrast(a, b):
    light, dark = sorted([luminance(a), luminance(b)], reverse=True)
    return (light + .05) / (dark + .05)


def ink_on(color):
    return '#FFFFFF' if contrast(color, '#FFFFFF') > contrast(color, '#171B18') else '#171B18'
