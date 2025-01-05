from flask import render_template, Blueprint, request

import pandas as pd 
from QualityAnalysis.flasktodo.graph import legend2M, legend1M, legend0M, ABlabels, Avalues2M, Avalues1M, Avalues0M, Bvalues2M, Bvalues1M, Bvalues0M, Plabels, Pvalues, svc_data_html, min_data_html
from QualityAnalysis.flasktodo.indicator import basic_function,pivot_function, hazard_function, ppm_function, ffr_function

hazard_json_path='QualityAnalysis/flasktodo/static/json/hazard.json'

def html_table(input_table):
    input_table_html=input_table.to_html()
    input_table_html=input_table_html.replace('border="1" class="dataframe"','id="datatablesSimple2"' )
    input_table_html=input_table_html.replace('<tr style="text-align: right;">','<tr>')
    input_table_html=input_table_html.replace('<th></th>','<th>No</th>')
    return input_table_html

bp = Blueprint('todo', __name__)

#check list만 여기서 sorting
@bp.route("/",methods=["POST","GET"])
def index():
    ####################### INITIAL #####################
    # symptoms
    initial_data=["DRAIN","EXPLANATION","EXTERIOR","FILLING","LEAK","LID","MISASSEMBLY","MOTOR","NOISE/VIBRATION","OTHER","PCB","RETURN"]

    # pivot chart --> datatablesSimple2
    sort_pivot=pivot_function(initial_data)
    sort_pivot_html=html_table(sort_pivot)

    # hazard graph
    hazard_table=hazard_function(initial_data) 
    # hazard xlabel name
    a=range(1,len(hazard_table)+1)
    hazard_table.insert(loc=0,column='label',value=a)
    json_value= hazard_table.to_json(orient='values')
    json_value=json_value.replace(',','","').replace(']","[','"],["').replace('[[','[["').replace(']]','"]]').replace(',"null"','')
    # hazard ylabel name 추가
    idx2=pd.DataFrame(basic_function(initial_data)[2][:-1]) #total 제외
    json_column=idx2.to_json(orient='values')
    json_column=json_column.replace('],[',',').replace(']]',']')
    json_sum=json_value.replace('[[',json_column+",[")
    # hazard write json file
    f=open(hazard_json_path, "w+")
    f.write(json_sum)
    f.close()

    # aar, ppm ---> datatablesSimple3
    aar_table=ppm_function(initial_data)
    aar_table_html=html_table(aar_table).replace('id="datatablesSimple2"','id="datatablesSimple3"')

    # ffr, fdr
    ffr_label=["Last 1M","Last 2M","Last 3M","Last 4M","Last 5M","Last6M","Last7M","Last8M","Last9M","Last10M","Last11M","Last12M"]
    ffr_result=ffr_function(initial_data)
    FFR1YValues=ffr_result[0]
    FFR1YLegend=ffr_result[1]
    FDR1YValues=ffr_result[2]
    FDR1YLegend=ffr_result[3]
    FFR2YValues=ffr_result[4]
    FFR2YLegend=ffr_result[5]
    FDR2YValues=ffr_result[6]
    FDR2YLegend=ffr_result[7]
    FFR3YValues=ffr_result[8]
    FFR3YLegend=ffr_result[9]
    FDR3YValues=ffr_result[10]
    FDR3YLegend=ffr_result[11]
    FFR4YValues=ffr_result[12]
    FFR4YLegend=ffr_result[13]
    FDR4YValues=ffr_result[14]
    FDR4YLegend=ffr_result[15]

    ####################### POST #####################
    #sort data - button click
    if request.method=='POST':
        if request.form.get('action1') == 'submit':
            # pivot chart --> datatablesSimple2
            input_data=request.form.getlist('symptom1')
            sort_pivot=pivot_function(input_data)
            sort_pivot_html=html_table(sort_pivot)


        elif request.form.get('action2') == 'submit':
            # hazard graph
            input_data=request.form.getlist('symptom2')
            hazard_table=hazard_function(input_data) 
            # hazard xlabel name
            a=range(1,len(hazard_table)+1)
            hazard_table.insert(loc=0,column='label',value=a)
            json_value= hazard_table.to_json(orient='values')
            json_value=json_value.replace(',','","').replace(']","[','"],["').replace('[[','[["').replace(']]','"]]').replace(',"null"','')
            # hazard ylabel name 추가
            idx2=pd.DataFrame(basic_function(initial_data)[2][:-1]) #total 제외
            json_column=idx2.to_json(orient='values')
            json_column=json_column.replace('],[',',').replace(']]',']')
            json_sum=json_value.replace('[[',json_column+",[")
            # hazard write json file
            f=open(hazard_json_path, "w+")
            f.write(json_sum)
            f.close()
            print("HH")

        
        elif request.form.get('action3') == 'submit':
            # aar, ppm ---> datatablesSimple3
            input_data=request.form.getlist('symptom3')
            aar_table=ppm_function(input_data)
            aar_table_html=html_table(aar_table).replace('id="datatablesSimple2"','id="datatablesSimple3"')
            print("AA")


        elif request.form.get('action4') == 'submit':
            # ffr, fdr
            input_data=request.form.getlist('symptom4')
            ffr_label=["Last 1M","Last 2M","Last 3M","Last 4M","Last 5M","Last6M","Last7M","Last8M","Last9M","Last10M","Last11M","Last12M"]
            ffr_result=ffr_function(input_data)
            FFR1YValues=ffr_result[0]
            FFR1YLegend=ffr_result[1]
            FDR1YValues=ffr_result[2]
            FDR1YLegend=ffr_result[3]
            FFR2YValues=ffr_result[4]
            FFR2YLegend=ffr_result[5]
            FDR2YValues=ffr_result[6]
            FDR2YLegend=ffr_result[7]
            FFR3YValues=ffr_result[8]
            FFR3YLegend=ffr_result[9]
            FDR3YValues=ffr_result[10]
            FDR3YLegend=ffr_result[11]
            FFR4YValues=ffr_result[12]
            FFR4YLegend=ffr_result[13]
            FDR4YValues=ffr_result[14]
            FDR4YLegend=ffr_result[15]
            print("KK")

        else:
            print("ERROR")


    return render_template('todo/index.html', ABlabels=ABlabels,
    Avalues2M=Avalues2M, Avalues1M=Avalues1M, Avalues0M=Avalues0M,
    Bvalues2M=Bvalues2M,Bvalues1M=Bvalues1M,Bvalues0M=Bvalues0M,
    legend2M=legend2M, legend1M=legend1M, legend0M=legend0M, 
    min_data_html=min_data_html, sort_pivot_html=sort_pivot_html, aar_table_html=aar_table_html,
    ffr_label=ffr_label,FFR1YValues=FFR1YValues, FFR1YLegend=FFR1YLegend,FDR1YValues=FDR1YValues,FDR1YLegend=FDR1YLegend,
    FFR2YValues=FFR2YValues, FFR2YLegend=FFR2YLegend,FDR2YValues=FDR2YValues,FDR2YLegend=FDR2YLegend,
    FFR3YValues=FFR3YValues, FFR3YLegend=FFR3YLegend,FDR3YValues=FDR3YValues,FDR3YLegend=FDR3YLegend,
    FFR4YValues=FFR4YValues, FFR4YLegend=FFR4YLegend,FDR4YValues=FDR4YValues,FDR4YLegend=FDR4YLegend)


@bp.route("/trend")
def trend():
    return render_template('todo/charts.html', ABlabels=ABlabels,
    Avalues2M=Avalues2M, Avalues1M=Avalues1M, Avalues0M=Avalues0M,
    Bvalues2M=Bvalues2M,Bvalues1M=Bvalues1M,Bvalues0M=Bvalues0M,
    Plabels=Plabels,Pvalues=Pvalues,
    legend2M=legend2M, legend1M=legend1M, legend0M=legend0M)

@bp.route("/list")
def list():
    return render_template('todo/tables.html',svc_data_html=svc_data_html)



@bp.route("/kpi",methods=["POST","GET"])
def kpi():
        ####################### INITIAL #####################
    # symptoms
    initial_data=["DRAIN","EXPLANATION","EXTERIOR","FILLING","LEAK","LID","MISASSEMBLY","MOTOR","NOISE/VIBRATION","OTHER","PCB","RETURN"]

    # pivot chart --> datatablesSimple2
    sort_pivot=pivot_function(initial_data)
    sort_pivot_html=html_table(sort_pivot)

    # hazard graph
    hazard_table=hazard_function(initial_data) 
    # hazard xlabel name
    a=range(1,len(hazard_table)+1)
    hazard_table.insert(loc=0,column='label',value=a)
    json_value= hazard_table.to_json(orient='values')
    json_value=json_value.replace(',','","').replace(']","[','"],["').replace('[[','[["').replace(']]','"]]').replace(',"null"','')
    # hazard ylabel name 추가
    idx2=pd.DataFrame(basic_function(initial_data)[2][:-1]) #total 제외
    json_column=idx2.to_json(orient='values')
    json_column=json_column.replace('],[',',').replace(']]',']')
    json_sum=json_value.replace('[[',json_column+",[")
    # hazard write json file
    f=open(hazard_json_path, "w+")
    f.write(json_sum)
    f.close()

    # aar, ppm ---> datatablesSimple3
    aar_table=ppm_function(initial_data)
    aar_table_html=html_table(aar_table).replace('id="datatablesSimple2"','id="datatablesSimple3"')

    # ffr, fdr
    ffr_label=["Last 1M","Last 2M","Last 3M","Last 4M","Last 5M","Last6M","Last7M","Last8M","Last9M","Last10M","Last11M","Last12M"]
    ffr_result=ffr_function(initial_data)
    FFR1YValues=ffr_result[0]
    FFR1YLegend=ffr_result[1]
    FDR1YValues=ffr_result[2]
    FDR1YLegend=ffr_result[3]
    FFR2YValues=ffr_result[4]
    FFR2YLegend=ffr_result[5]
    FDR2YValues=ffr_result[6]
    FDR2YLegend=ffr_result[7]
    FFR3YValues=ffr_result[8]
    FFR3YLegend=ffr_result[9]
    FDR3YValues=ffr_result[10]
    FDR3YLegend=ffr_result[11]
    FFR4YValues=ffr_result[12]
    FFR4YLegend=ffr_result[13]
    FDR4YValues=ffr_result[14]
    FDR4YLegend=ffr_result[15]

    ####################### POST #####################
    #sort data - button click
    if request.method=='POST':
        if request.form.get('action1') == 'submit':
            # pivot chart --> datatablesSimple2
            input_data=request.form.getlist('symptom1')
            sort_pivot=pivot_function(input_data)
            sort_pivot_html=html_table(sort_pivot)


        elif request.form.get('action2') == 'submit':
            # hazard graph
            input_data=request.form.getlist('symptom2')
            hazard_table=hazard_function(input_data) 
            # hazard xlabel name
            a=range(1,len(hazard_table)+1)
            hazard_table.insert(loc=0,column='label',value=a)
            json_value= hazard_table.to_json(orient='values')
            json_value=json_value.replace(',','","').replace(']","[','"],["').replace('[[','[["').replace(']]','"]]').replace(',"null"','')
            # hazard ylabel name 추가
            idx2=pd.DataFrame(basic_function(initial_data)[2][:-1]) #total 제외
            json_column=idx2.to_json(orient='values')
            json_column=json_column.replace('],[',',').replace(']]',']')
            json_sum=json_value.replace('[[',json_column+",[")
            # hazard write json file
            f=open(hazard_json_path, "w+")
            f.write(json_sum)
            f.close()
            print("HH")

        
        elif request.form.get('action3') == 'submit':
            # aar, ppm ---> datatablesSimple3
            input_data=request.form.getlist('symptom3')
            aar_table=ppm_function(input_data)
            aar_table_html=html_table(aar_table).replace('id="datatablesSimple2"','id="datatablesSimple3"')
            print("AA")


        elif request.form.get('action4') == 'submit':
            # ffr, fdr
            input_data=request.form.getlist('symptom4')
            ffr_label=["Last 1M","Last 2M","Last 3M","Last 4M","Last 5M","Last6M","Last7M","Last8M","Last9M","Last10M","Last11M","Last12M"]
            ffr_result=ffr_function(input_data)
            FFR1YValues=ffr_result[0]
            FFR1YLegend=ffr_result[1]
            FDR1YValues=ffr_result[2]
            FDR1YLegend=ffr_result[3]
            FFR2YValues=ffr_result[4]
            FFR2YLegend=ffr_result[5]
            FDR2YValues=ffr_result[6]
            FDR2YLegend=ffr_result[7]
            FFR3YValues=ffr_result[8]
            FFR3YLegend=ffr_result[9]
            FDR3YValues=ffr_result[10]
            FDR3YLegend=ffr_result[11]
            FFR4YValues=ffr_result[12]
            FFR4YLegend=ffr_result[13]
            FDR4YValues=ffr_result[14]
            FDR4YLegend=ffr_result[15]
            print("KK")

        else:
            print("ERROR")


    return render_template('todo/quality.html', sort_pivot_html=sort_pivot_html, aar_table_html=aar_table_html,
    ffr_label=ffr_label,FFR1YValues=FFR1YValues, FFR1YLegend=FFR1YLegend,FDR1YValues=FDR1YValues,FDR1YLegend=FDR1YLegend,
    FFR2YValues=FFR2YValues, FFR2YLegend=FFR2YLegend,FDR2YValues=FDR2YValues,FDR2YLegend=FDR2YLegend,
    FFR3YValues=FFR3YValues, FFR3YLegend=FFR3YLegend,FDR3YValues=FDR3YValues,FDR3YLegend=FDR3YLegend,
    FFR4YValues=FFR4YValues, FFR4YLegend=FFR4YLegend,FDR4YValues=FDR4YValues,FDR4YLegend=FDR4YLegend)

#card
@bp.route("/report")

def report():
    return render_template('card/report.html')

@bp.route("/email")

def email():
    return render_template('card/email.html')

@bp.route("/logic")

def logic():
    return render_template('card/dataframe.html')


#layout
@bp.route("/layout_static")

def layout_static():
    return render_template('windowskin/layout-static.html')

@bp.route("/layout_sidenav")

def layout_sidenav():
    return render_template('windowskin/layout-sidenav-light.html')

#error
@bp.route("/error_401")

def error_401():
    return render_template('error/401.html')

@bp.route("/error_404")

def error_404():
    return render_template('error/404.html')

@bp.route("/error_500")

def error_500():
    return render_template('error/500.html')
if __name__ == "__main__":
    bp.run(debug=True)