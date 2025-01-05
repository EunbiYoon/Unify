from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class VideoSurvey(db.Model):
    __tablename__ = 'Video Survey'
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(200), nullable=False)
    dealer = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text(), nullable=False)




