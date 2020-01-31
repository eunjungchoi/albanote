## 알바노트

## 사용 기술
 * Python >= 3.6
 * Django >= 2.2
 * Django REST Framework
  
## 로컬 개발 세팅

```bash
(Mac OS 기준)
brew install postgres
brew services start postgresql
```
파이썬 가상환경 설치
```bash
brew install pyenv 
brew install readline xz
pyenv install 3.6.5
pyenv virtualenv 3.6.5 venv-3.6.5
```
(가상환경의 생성과 삭제는 시스템의 어느 위치에서 실행해도 상관 없음)

해당 프로젝트 디렉토리에서 가상환경 지정
```bash
pyenv local venv-3.6.5
pyenv versions
```

패키지 설치
```bash
pip install -r requirements.txt
```

DB 설정
```bash
./manage.py migrate
```

어드민 계정 생성
```bash
./manage.py createsuperuser
```

서버 띄우기
```bash
./manage.py runserver
```
다음 주소에 접속해본다. http://localhost:8000/admin/ 
