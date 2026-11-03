"""Run explicitly against the local migrated API; never touches production."""
import json
import secrets
import requests

URL = 'http://127.0.0.1:5175'
PASSWORD = secrets.token_urlsafe(24)
sessions = []


def post(s, path, payload, status=200):
    response = s.post(URL+path, json=payload, timeout=30)
    assert response.status_code==status, (response.status_code, response.text[:300])
    return response.json()


def change(s, action, expected_status=200, **values):
    return post(s, '/api/data', {'action':action, **values}, expected_status)


def data(s):
    r = s.get(URL+'/api/data', timeout=30)
    r.raise_for_status()
    return r.json()


def account():
    s = requests.Session()
    s.headers['Origin'] = URL
    email = 'schedule-'+secrets.token_hex(6)+'@example.test'
    post(s, '/api/auth', {'action':'register','email':email,'password':PASSWORD,'passwordConfirm':PASSWORD,'name':'로컬 검증'}, status=201)
    sessions.append(s)
    return s, email


try:
    a, email = account()
    b, _ = account()
    assert 'schedule-v1' in data(a)['capabilities']
    def add(title, **values):
        change(a, 'task.add', title=title, date='2026-11-03', **values)
        return next(t for t in data(a)['tasks'] if t['title']==title)
    loose = add('loose', timeBand='night')
    timed = add('timed', timeBand='morning', plannedStart='14:00', plannedEnd='15:00', visibility='shared')
    fixed = add('fixed', plannedStart='10:00', isFixed=True)
    other = add('other')
    assert loose['time_band']=='night' and not loose['planned_start']
    assert timed['time_band']=='afternoon'
    shared = next(t for t in data(b)['sharedTasks'] if t['id']==timed['id'])
    assert shared['planned_start']=='' and shared['time_band']=='anytime'
    change(a, 'task.update', id=timed['id'], status='partial', actualStart='16:00', actualEnd='16:20', note='조금 진행', shareTime=True)
    shared = next(t for t in data(b)['sharedTasks'] if t['id']==timed['id'])
    assert shared['actual_start']=='16:00' and shared['status']=='partial'
    change(b, 'task.update', expected_status=404, id=timed['id'], title='forbidden')
    change(a, 'task.update', expected_status=400, id=timed['id'], plannedStart='16:00')
    change(a, 'task.add', expected_status=400, title='bad date', date='2026-02-30')
    change(a, 'task.reschedule', expected_status=409, ids=[loose['id'],fixed['id']], fromDate='2026-11-03', date='2026-11-04')
    assert next(t for t in data(a)['tasks'] if t['id']==loose['id'])['date']=='2026-11-03'
    change(b, 'task.reschedule', expected_status=409, ids=[loose['id']], fromDate='2026-11-03', date='2026-11-04')
    change(a, 'task.reschedule', ids=[loose['id'],other['id']], fromDate='2026-11-03', date='2026-11-04')
    assert all(t['date']=='2026-11-04' for t in data(a)['tasks'] if t['id'] in (loose['id'],other['id']))
    change(b, 'reaction', kind='task', id=timed['id'], emoji='\U0001f49a')
    assert any(r['task_id']==timed['id'] for r in data(a)['taskReactions'])
    change(b, 'reaction', kind='task', id=timed['id'], emoji='\U0001f49a')
    assert not any(r['task_id']==timed['id'] for r in data(a)['taskReactions'])
    theme = {'background':'#F3F1EC','text':'#343B38','card':'#FAF9F6','calendar':'#E7EAE3','accent':'#526657','font':'gowun'}
    change(a, 'theme.save', theme=theme)
    post(a, '/api/auth', {'action':'logout'})
    post(a, '/api/auth', {'action':'login','email':email,'password':PASSWORD})
    refreshed = data(a)
    assert json.loads(refreshed['me']['theme'])==theme
    assert next(t for t in refreshed['tasks'] if t['id']==timed['id'])['actual_end']=='16:20'
    change(a, 'task.update', id=timed['id'], visibility='private')
    assert not any(t['id']==timed['id'] for t in data(b)['sharedTasks'])
    print('PASS: local API persistence, timing validation, privacy, ownership, atomic rescheduling, reactions, theme and relogin')
finally:
    for s in sessions:
        try:
            change(s, 'account.delete', password=PASSWORD)
        finally:
            s.close()
