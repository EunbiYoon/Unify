from datetime import datetime
from flask import render_template, url_for, redirect, Blueprint, abort, request, url_for, redirect
from VideoTutorial.flaskapp.models import db, VideoSurvey
# from flaskapp.models import db, VideoSurvey

bp = Blueprint('action', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/submit', methods=('POST',))
def submit():
    try:
        product = request.form.get('product')
        dealer = request.form.get('dealer')
        rating = request.form.get('rating')
        review = request.form.get('review')

        # 필수 입력값 검증
        if not all([product, dealer, rating, review]):
            abort(400, "모든 필드를 입력해야 합니다.")

        # 데이터베이스에 추가
        data = VideoSurvey(product=product, dealer=dealer, rating=int(rating), review=review)
        db.session.add(data)
        db.session.commit()

        return render_template('success.html', data=data)
    except Exception as e:
        db.session.rollback()
        return f"데이터베이스 오류: {str(e)}", 500


#from video template to go back homepage
@bp.route('/home', methods=['POST'])
def home():      
    return redirect(url_for('.index')) # do something


# top loader template render
@bp.route('/topnoise', methods=('POST',))
def topnoise():
    return render_template('tl/noise.html') # do something

@bp.route('/topcloth', methods=('POST',))
def topcloth():  
    return render_template('tl/clothing.html') # do something

@bp.route('/topcycle', methods=('POST',))
def topcycle():         
    return render_template('tl/cycle.html') # do something

@bp.route('/topleak', methods=('POST',))
def topleak():  
    return render_template('tl/leak.html') # do something

@bp.route('/toperror', methods=('POST',))
def toperror():  
    return render_template('tl/error.html') # do something'

@bp.route('/topfill', methods=('POST',))
def topfill():  
    return render_template('tl/filling.html') # do something

@bp.route('/topdrain', methods=('POST',))
def topdrain():  
    return render_template('tl/drainage.html') # do something

@bp.route('/topdispense', methods=('POST',))
def topdispense():  
    return render_template('tl/dispenser.html') # do something

@bp.route('/topdoor', methods=('POST',))
def topdoor():  
    return render_template('tl/door.html') # do something

@bp.route('/toppower', methods=('POST',))
def toppower():  
    return render_template('tl/power.html') # do something

@bp.route('/topsmell', methods=('POST',))
def topsmell():  
    return render_template('tl/smell.html') # do something

@bp.route('/topthinq', methods=('POST',))
def topthinq():      
    return render_template('tl/thinq.html') # do something


#front loader template render
@bp.route('/frontnoise', methods=('POST',))
def frontnoise():
    return render_template('fl/noise.html') # do something

@bp.route('/frontcloth', methods=('POST',))
def frontcloth():   
    return render_template('fl/clothing.html') # do something

@bp.route('/frontcycle', methods=('POST',))
def frontcycle():         
    return render_template('fl/cycle.html') # do something

@bp.route('/fronfleak', methods=('POST',))
def fronfleak():  
    return render_template('fl/leak.html') # do something

@bp.route('/fronterror', methods=('POST',))
def fronterror():  
    return render_template('fl/error.html') # do something'

@bp.route('/frontfill', methods=('POST',))
def frontfill():  
    return render_template('fl/filling.html') # do something

@bp.route('/frontdrain', methods=('POST',))
def frontdrain():  
    return render_template('fl/drainage.html') # do something

@bp.route('/frontdispense', methods=('POST',))
def frontdispense():  
    return render_template('fl/dispenser.html') # do something

@bp.route('/frontdoor', methods=('POST',))
def frontdoor():  
    return render_template('fl/door.html') # do something

@bp.route('/frontpower', methods=('POST',))
def frontpower():  
    return render_template('fl/power.html') # do something

@bp.route('/frontsmell', methods=('POST',))
def frontsmell():  
    return render_template('fl/smell.html') # do something

@bp.route('/frontthinq', methods=('POST',))
def frontthinq():      
    return render_template('fl/thinq.html') # do something

