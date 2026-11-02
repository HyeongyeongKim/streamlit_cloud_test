"""Per-browser-session client; never place this client in a shared Streamlit cache."""
import os
import requests

API_URL = os.environ.get('GARDEN_API_URL', 'https://oneul-garden.hyeongyeong.chatgpt.site').rstrip('/')

class APIError(Exception):
    def __init__(self, message, status=0):
        super().__init__(message)
        self.status = status

class GardenClient:
    def __init__(self):
        self.http = requests.Session()
        self.http.headers.update({'User-Agent': 'Mozilla/5.0 GardenStreamlit/1.0', 'Origin': API_URL})

    def request(self, method, path, **kwargs):
        try:
            response = self.http.request(method, API_URL + path, timeout=30, **kwargs)
        except requests.RequestException as exc:
            raise APIError('저장 서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.') from exc
        if not response.ok:
            try:
                message = response.json().get('error', '요청을 처리하지 못했습니다.')
            except ValueError:
                message = '저장 서버 응답을 확인하지 못했습니다. 잠시 후 다시 시도해 주세요.'
            raise APIError(message, response.status_code)
        return response

    def data(self):
        return self.request('GET', '/api/data').json()

    def auth(self, action, **values):
        return self.request('POST', '/api/auth', json={'action': action, **values}).json()

    def change(self, action, **values):
        return self.request('POST', '/api/data', json={'action': action, **values}).json()

    def upload(self, file):
        if file.size > 5_000_000:
            raise APIError('사진은 5MB 이하로 올려 주세요.')
        return self.request('POST', '/api/photos', files={'file': (file.name, file.getvalue(), file.type)}).json()['key']

    def photo(self, key):
        return self.request('GET', '/api/photos', params={'key': key}).content

    def close(self):
        self.http.close()
