import os
import requests
from flask import Flask, render_template
from .todo import bp  # ✅ 상대경로 import (배포 시 필수)


def handle_401(e):
    return render_template('error/401.html'), 401

def handle_404(e):
    return render_template('error/404.html'), 404

def handle_500(e):
    return render_template('error/500.html'), 500


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # 에러 핸들러 등록
    app.register_error_handler(401, handle_401)
    app.register_error_handler(404, handle_404)
    app.register_error_handler(500, handle_500)

    # 블루프린트 등록
    app.register_blueprint(bp, url_prefix='/qualityanalysisdashboard')

    return app
