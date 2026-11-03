import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from garden_api import GardenClient

class StreamlitTests(unittest.TestCase):
    def test_guest_and_pages(self):
        app = AppTest.from_file('streamlit_cloud.py').run()
        self.assertEqual(len(app.exception), 0)
        app.radio[0].set_value('회원가입').run()
        self.assertEqual(len(app.text_input), 4)
        self.assertEqual(len(app.exception), 0)
        data = {'me': {'name': '테스트', 'theme': '{}'}, **{key: [] for key in ['tasks', 'habits', 'checks', 'diaries', 'taskReactions', 'diaryReactions', 'comments', 'sharedTasks', 'sharedDiaries', 'feedTaskReactions', 'feedDiaryReactions', 'feedComments']}}
        with patch.object(GardenClient, 'data', return_value=data):
            app.session_state['logged_in'] = True
            app.run()
            for page in ['오늘 · 일정', '내 기록', '일기', '습관', '함께', '화면 설정', '계정']:
                app.sidebar.radio[0].set_value(page).run()
                self.assertEqual(len(app.exception), 0, page)
            # Exercise populated owner/feed cards, including widget IDs.
            task = {'id': 't1', 'title': '산책', 'date': '2026-11-02', 'status': 'todo', 'visibility': 'shared', 'owner_name': '친구'}
            diary = {'id': 'd1', 'date': '2026-11-02', 'mood': 'good', 'body': '좋은 하루', 'visibility': 'shared', 'owner_name': '친구', 'photo_key': None}
            data['tasks'] = [task]
            data['diaries'] = [diary]
            data['sharedTasks'] = [dict(task, id='t2')]
            data['sharedDiaries'] = [dict(diary, id='d2')]
            data['habits'] = [{'id': 'h1', 'title': '물 마시기', 'days': '0,1,2,3,4,5,6'}]
            data['capabilities'] = ['schedule-v1']
            for page in ['오늘 · 일정', '내 기록', '일기', '습관', '함께']:
                app.sidebar.radio[0].set_value(page).run()
                if page == '오늘 · 일정':
                    from datetime import date
                    app.date_input(key='selected_date').set_value(date(2026, 11, 2)).run()
                self.assertEqual(len(app.exception), 0, page)

if __name__ == '__main__':
    unittest.main()
