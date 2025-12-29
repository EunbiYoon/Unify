# How to run flask in QualityAnalysis
1. Move location to QualityAnalysis and make sure you are in virtual environment(venv)
2. todo.py, __init__.py need to change like this
    => from QualityAnalysis.flasktodo.graph  ->  from flasktodo.graph
    => Totally 5 points
        [todo.py]
        1) from QualityAnalysis.flasktodo.graph import legend2M, legend1M, legend0M, ABlabels, Avalues2M, Avalues1M, Avalues0M, Bvalues2M, Bvalues1M,...
        2) from QualityAnalysis.flasktodo.indicator import basic_function,pivot_function, hazard_function, ppm_function, ffr_function
        3) hazard_json_path='QualityAnalysis/flasktodo/static/json/hazard.json'
        [__init__.py]
        4) from QualityAnalysis.flasktodo import todo
        5) from QualityAnalysis.flasktodo.todo import bp
3. Run "flask run"
4. Visit this, http://127.0.0.1:5000/qualityanalysisdashboard/
5. If you want to change to visit, http://127.0.0.1:5000, to see home page then remove url_prefix in __init__.py
    => todo.register_blueprint(bp,url_prefix='/qualityanalysisdashboard')

# How to run flask in VideoTutorial
1. Move location to VideoTutorial and make sure you are in virtual environment(venv)
2. action.py, __init__.py need to change like this
    => from QualityAnalysis.flasktodo.graph  ->  from flasktodo.graph
    => Totally 5 points
        [action.py]
        1) from VideoTutorial.flaskapp.models import db, VideoSurvey
        [__init__.py]
        2) from VideoTutorial.flaskapp import action    
        3) from VideoTutorial.flaskapp.models import db


# SQlite Query
## get into query
1. sqlite3 db.sqlite3 
## check all the table
2. .tables
## based on id, delete 
### if you delete division, all related will delete
3. DELETE FROM account_division WHERE id >= 3; 
## reset sequence
4. DELETE FROM sqlite_sequence WHERE name = 'account_division';