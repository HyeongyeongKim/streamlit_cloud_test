import json
import unittest
from datetime import datetime, time
from zoneinfo import ZoneInfo
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from garden_api import GardenClient, APIError
from planner import BASE


def empty_data():
    return {'capabilities':['schedule-v1'], 'me':{'id':'me','name':'테스트','theme':json.dumps(BASE)}, **{k:[] for k in ['tasks','habits','checks','diaries','taskReactions','diaryReactions','comments','sharedTasks','sharedDiaries','feedTaskReactions','feedDiaryReactions','feedComments']}}


def widget(items, label):
    return next(x for x in items if x.label==label)


class ScheduleUITests(unittest.TestCase):
    def setUp(self):
        self.data = empty_data()
        self.patcher = patch.object(GardenClient, 'data', side_effect=lambda:self.data)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.change_patch = patch.object(GardenClient, 'change', return_value={'ok':True})
        self.change = self.change_patch.start()
        self.addCleanup(self.change_patch.stop)
        self.app = AppTest.from_file('streamlit_cloud.py').run()
        self.app.session_state['logged_in'] = True
        self.app.run()

    def task(self, **values):
        return {'id':'t1','date':datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat(),'title':'책 읽기','status':'todo','visibility':'private','time_band':'morning', **values}

    def test_add_loose_and_exact_schedule_payload(self):
        widget(self.app.text_input, '새로운 할 일').set_value('산책')
        self.app.selectbox(key='new_band').set_value('night')
        widget(self.app.button, '일정 추가').click().run()
        self.assertEqual(len(self.app.exception), 0)
        payload = self.change.call_args.kwargs
        self.assertEqual(payload['timeBand'], 'night')
        self.assertEqual(payload['plannedStart'], '')
        self.assertEqual(payload['visibility'], 'private')
        widget(self.app.text_input, '새로운 할 일').set_value('수업')
        self.app.time_input(key='new_start').set_value(time(14))
        self.app.time_input(key='new_end').set_value(time(15))
        self.app.checkbox(key='new_fixed').check()
        widget(self.app.button, '일정 추가').click().run()
        self.assertEqual(self.change.call_args.kwargs['timeBand'], 'afternoon')
        self.assertTrue(self.change.call_args.kwargs['isFixed'])

    def test_invalid_input_does_not_save(self):
        widget(self.app.text_input, '새로운 할 일').set_value('수업')
        self.app.time_input(key='new_start').set_value(time(15))
        self.app.time_input(key='new_end').set_value(time(14))
        widget(self.app.button, '일정 추가').click().run()
        self.change.assert_not_called()
        self.assertGreater(len(self.app.warning), 0)
        self.assertEqual(widget(self.app.text_input, '새로운 할 일').value, '수업')

    def test_partial_and_actual_record(self):
        self.data['tasks'] = [self.task()]
        self.app.run()
        self.app.button(key='partial_t1').click().run()
        self.assertEqual(self.change.call_args.kwargs['status'], 'partial')
        widget(self.app.time_input, '실제 시작 (선택)').set_value(time(16))
        widget(self.app.time_input, '실제 종료 (선택)').set_value(time(16,20))
        widget(self.app.text_area, '짧은 기록').set_value('조금 읽었어요')
        widget(self.app.button, '변경 저장').click().run()
        self.assertEqual(self.change.call_args.kwargs['actualStart'], '16:00')
        self.assertEqual(self.change.call_args.kwargs['note'], '조금 읽었어요')

    def test_lighten_excludes_fixed_done_and_recorded(self):
        self.data['tasks'] = [self.task(), self.task(id='t2',is_fixed=1,planned_start='10:00'), self.task(id='t3',status='done'), self.task(id='t4',actual_start='09:00')]
        self.app.run()
        select = widget(self.app.multiselect, '다른 날로 옮길 일')
        self.assertEqual(len(select.options), 1)
        select.set_value(['t1'])
        widget(self.app.button, '선택한 일정 옮기기').click().run()
        self.assertEqual(self.change.call_args.args, ('task.reschedule',))
        self.assertEqual(self.change.call_args.kwargs['ids'], ['t1'])

    def test_theme_persists_font_and_custom_colors(self):
        self.app.sidebar.radio[0].set_value('화면 설정').run()
        widget(self.app.color_picker, '배경').set_value('#EEEAE1')
        widget(self.app.selectbox, '글꼴').set_value('gowun')
        widget(self.app.button, '내 화면 저장').click().run()
        theme = self.change.call_args.kwargs['theme']
        self.assertEqual(theme['font'], 'gowun')
        self.assertEqual(theme['background'], '#EEEAE1')
        self.data['me']['theme'] = json.dumps(theme)
        self.app.run()
        self.assertEqual(widget(self.app.selectbox, '글꼴').value, 'gowun')
        self.assertEqual(widget(self.app.color_picker, '배경').value, '#EEEAE1')

    def test_reaction_is_text_and_compatible_with_existing_api(self):
        self.data['sharedTasks'] = [self.task(owner_name='친구',visibility='shared')]
        self.app.sidebar.radio[0].set_value('함께').run()
        widget(self.app.button, '응원해요 · 0').click().run()
        self.assertEqual(self.change.call_args.args, ('reaction',))
        self.assertEqual(self.change.call_args.kwargs['emoji'], '\U0001f49a')

    def test_old_server_and_failure_do_not_claim_new_save(self):
        self.data.pop('capabilities')
        self.app.run()
        self.assertEqual(len(self.app.time_input), 0)
        self.change.side_effect = APIError('저장 실패')
        widget(self.app.text_input, '새로운 할 일').set_value('산책')
        widget(self.app.button, '일정 추가').click().run()
        self.assertEqual(len(self.app.success), 0)
        self.assertEqual(self.app.error[0].value, '저장 실패')
