# 오늘의 정원 — Streamlit

배포 주소: https://codeithyeongyeong.streamlit.app/

## 실행 및 배포

- GitHub 저장소: HyeongyeongKim/streamlit_cloud_test
- 브랜치: main
- Streamlit Community Cloud 엔트리: streamlit_cloud.py
- Python 3.11 이상 권장

```sh
pip install -r requirements.txt
streamlit run streamlit_cloud.py
```

GitHub에 푸시하면 이 저장소에 연결된 기존 Streamlit 앱이 변경사항을 반영합니다.

## 구조

화면은 Python/Streamlit입니다. 회원 인증, 계정별 일정·일기·습관, 사진, 공유 반응은 기존 오늘의 정원 HTTPS API를 호출합니다. 데이터는 기존 서버의 D1/R2에 저장되므로 Streamlit 재시작 시 사라지지 않습니다. 기존 이메일 계정도 사용할 수 있습니다. Sites의 기존 백엔드를 삭제하면 저장 기능이 중단됩니다.

기본 API: https://oneul-garden.hyeongyeong.chatgpt.site

서버 이전 시 환경변수 GARDEN_API_URL로 변경할 수 있습니다. API 세션은 방문자별 st.session_state에 보관하며 전역 캐시로 공유하지 않습니다. 브라우저 새로고침 후 재로그인이 필요할 수 있습니다. 비밀번호 재설정 메일과 이메일 소유 확인 메일은 아직 연결하지 않았습니다.

## 기능과 화면

- 이메일 회원가입·로그인·로그아웃·비밀번호 확인 후 탈퇴
- 날짜 선택 달력과 월간 기록 요약, 완료/못함, 다음 날 또는 지정일로 이동
- 사진·감정·글 일기, 수정·삭제, 선택적 공개와 댓글
- 반복 요일 습관 체크, 모두 완료하면 축하 표시
- 공유 기록별 반응과 일기 댓글
- 추천 팔레트와 색 선택 도구, 무료 한국어 글꼴
- 모바일 폭에 맞는 화면 및 사이드바 메뉴

일정은 특정 날짜에 해야 하는 일, 습관은 선택한 요일마다 쌓는 실천 기록으로 구분합니다. 기록은 기본 비공개이며 공유를 선택한 항목만 다른 회원에게 노출됩니다.

## 검증

```sh
python -m unittest discover -s tests -v
```

Streamlit AppTest로 비회원 로그인/가입과 로그인 후 모든 메뉴, 기록이 있는 화면을 확인합니다. 배포 전 별도 일회용 계정으로 실제 저장 서버의 가입, 로그인 세션, 일정 저장, 로그아웃, 재로그인, 탈퇴를 검증합니다.
