
import os

from flask import Flask, render_template
from QualityAnalysis.flasktodo import todo
from QualityAnalysis.flasktodo.todo import bp
import requests


def handle_401(e):
    return render_template('error/401.html'), 401

def handle_404(e):
    return render_template('error/404.html'), 404

def handle_500(e):
    return render_template('error/500.html'), 500

def create_app():
    todo = Flask(__name__, instance_relative_config=True)

    todo.register_error_handler(401, handle_401)
    todo.register_error_handler(404, handle_404)
    todo.register_error_handler(500, handle_500)
    
    #### Flask URL 선언 ####
    todo.register_blueprint(bp,url_prefix='/qualityanalysisdashboard')
    
    return todo
