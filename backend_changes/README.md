# schedule-v1 저장 서버 변경

현재 Streamlit 앱이 사용하는 별도 Sites 백엔드용 패치입니다.

- 프로젝트: `appgprj_6ae86586402481919c53784e4e0070a7`
- 기존 API: `https://oneul-garden.hyeongyeong.chatgpt.site`
- 로컬 소스: `sites/oneul-garden` (별도 Git 저장소, 상위 저장소에서는 ignore)
- 이 폴더의 `schedule-v1.patch`에 백엔드 변경 전체를 보존합니다.
- 로컬 소스에는 이미 패치가 적용되어 있습니다. 다시 적용하지 마세요.

## 변경

`tasks`에 `time_band`, `planned_start`, `planned_end`, `actual_start`, `actual_end`,
`is_fixed`, `share_time`, `note`를 추가합니다. 기존 데이터는 삭제하지 않고 `anytime`
(오늘 중), 빈 시각, 시간 비공개로 이행합니다.

`task.add` / `task.update`는 `timeBand`, `plannedStart`, `plannedEnd`, `actualStart`,
`actualEnd`, `isFixed`, `shareTime`, `note`를 받습니다. `partial`, `skipped` 상태가 추가됩니다.
시작 시각이 있으면 오전(00–12), 오후(12–18), 밤(18–24)으로 분류합니다.
시작 없는 종료, 역전 구간, 잘못된 날짜를 거부합니다. 자정을 넘는 일정은 날짜별로 나눕니다.

`task.reschedule`은 `ids`, `fromDate`, `date`를 받습니다. 해당 사용자 소유이고,
기존 날짜가 일치하며, 아직 예정 상태이고, 고정 약속/실제 기록이 없는 일정만 옮깁니다.
일부만 옮기는 대신 단일 원자적 SQL 문으로 전체 조건을 검증합니다. 충돌은 409입니다.

공유 시 `share_time=0`이면 시각·시간대·고정 약속 여부는 API 응답에서도 숨깁니다.
반응의 기존 식별자는 보존하고 Streamlit 화면에서 텍스트로 표시합니다.

## 배포 상태와 순서

2026-11-03: 로컬 구현, TypeScript 검사, 프로덕션 빌드, 로컬 D1에 대한 실제 API 검증 완료.
원격 소스 동기화는 sandbox 네트워크 제한으로 실패했고, 승격 실행 재시도는 기본 PowerShell
실행 파일 접근 거부(CreateProcessW error 5)로 시작되지 못했습니다. **운영 배포는 미완료입니다.**

1. Sites 스킬의 기존 프로젝트 열기 절차로 최신 소스를 동기화합니다. 현재 로컬 변경을 보존하세요.
2. 새 체크아웃에서는 `git apply --check <이 폴더의 schedule-v1.patch>` 후 패치를 적용합니다.
   이미 적용된 체크아웃에서는 `git apply --reverse --check ...`로 확인만 합니다.
3. `node node_modules/typescript/bin/tsc --noEmit`과 Sites 빌드 도구로 검사합니다.
4. Sites source helper로 소스 commit/push/패키징 후 기존 공개 범위를 유지하여 게시합니다.
   배포 패키지에 `drizzle/0002_common_omega_red.sql`과 migration 메타데이터를 포함해야 합니다.
5. 인증된 `/api/data` 응답에 `capabilities: ["schedule-v1"]`이 포함되는지 확인합니다.
6. Streamlit 변경을 GitHub에 반영합니다. 새 API가 먼저 배포되지 않으면 UI는 기존 기능만
   제공하며 시간대 입력을 비활성화합니다. 지원하지 않는 서버에 새 값을 조용히 버리며 저장하지 않습니다.

기존 Sites의 별도 React 화면 디자인은 이번 Streamlit 개편 대상에 포함하지 않았습니다.

## 로컬 검증

로컬 서버는 127.0.0.1:5175에서 실행합니다. 기존 로컬 migration 적용 상태를 확인한 뒤
미적용 migration만 README의 Wrangler 로컬 명령으로 적용하세요.

```powershell
# sites/oneul-garden에서
node scripts/run-framework.mjs dev --hostname 127.0.0.1 --port 5175

# 상위 Streamlit 프로젝트에서, 다른 터미널
$env:GARDEN_API_URL='http://127.0.0.1:5175'
python -m streamlit run streamlit_cloud.py
python tests/integration_schedule.py
```

통합 검사는 고정된 로컬 주소에 일회용 계정 두 개를 생성하고 저장·공개 범위·소유권·반응
토글·재로그인을 검증한 뒤 해당 계정을 제거합니다. 운영 서버를 대상으로 실행하지 않습니다.
