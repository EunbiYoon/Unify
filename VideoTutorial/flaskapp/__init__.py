import os
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_migrate import Migrate    
from VideoTutorial.flaskapp.action import bp     
from VideoTutorial.flaskapp.models import db
# from flaskapp.action import bp    
# from flaskapp.models import db


# .env 파일 로드
dotenv_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    '..',
    '.env'
)
load_dotenv(dotenv_path=dotenv_path)

# Migrate 인스턴스 생성
migrate = Migrate()

# 404 에러 핸들러
def handle_404(e):
    return render_template('404.html'), 404

# Flask 애플리케이션 팩토리 패턴
def create_app():
    """Flask 애플리케이션 팩토리"""
    app = Flask(__name__, instance_relative_config=True)
    
    # 환경 변수 로드
    try:
        app.config.from_mapping(
            SECRET_KEY=os.environ['SECRET_KEY'],
            SQLALCHEMY_DATABASE_URI=os.environ['SQLALCHEMY_DATABASE_URI'],
            SQLALCHEMY_TRACK_MODIFICATIONS=False
        )
    except KeyError as e:
        raise RuntimeError(f"{e} 환경 변수가 누락되었습니다. .env 파일을 확인하세요!")

    # 404 에러 핸들러 등록
    app.register_error_handler(404, handle_404)

    # 데이터베이스 초기화 및 마이그레이션 연결
    db.init_app(app)
    migrate.init_app(app, db)

    # 블루프린트 등록
    app.register_blueprint(bp,url_prefix='/lgsupportvideotutorial')
    
    return app
