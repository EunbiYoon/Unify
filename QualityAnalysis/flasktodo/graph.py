from random import*
import numpy as np 
import pandas as pd
from datetime import datetime, timedelta, date

#1 Year Sales, SVC 마지막 날 dataframe 만들기
today=date.today()
YearNdate=pd.DataFrame(columns=["Month","Ndate"])
for i in range(12):
    condition=int(today.strftime('%m'))-i
    if condition<=0:
        condition = condition+12
    YearNdate.at[i,"Month"]=condition

#lunar year
today=date.today()
lunaryear=int(today.strftime('%y'))%4

# 달의 마지막날 추출
for i in range(12):
    condition=YearNdate.at[i,"Month"]
    a=0
    if condition==1 or condition==3 or condition==5 or condition==7 or condition==8 or condition==10 or condition==12:
        a=31
    elif condition==4 or condition==6 or condition==9 or condition==11:
        a=30
    elif condition==2:
        today=date.today()-timedelta(days=i*30)
        lunaryear=int(today.strftime('%y'))%4
        if lunaryear==0:
            a=29
        else:
            a=28
    else:
        print("Year End Month Error")
    YearNdate.at[i,"Ndate"]=a

############## YearSalesData
# 1 Year Sales data
YearSalesData=pd.DataFrame()
for i in range(12):
    for j in range(YearNdate.at[11-i,"Ndate"]):
        YearSalesData.at[j,i]=randint(0,500)

# Total Sales, Total SVC Total Prod
TotalSales=int(YearSalesData.sum().sum())
TotalSVC=randint(4000,6000)
TotalProd=int(TotalSales+randint(0,10000))

################ svc_data
#Symptom
letter=["DRAIN","EXPLANATION","INSTALLATION","PULSATOR/AGITATOR","EXTERIOR","FILLING","LEAK","LID","MISASSEMBLY","MOTOR","NOISE/VIBRATION","OTHER","PCB","Return"]
symptom=' '.join(choice(letter) for i in range(TotalSVC))

detail_letter=["Defective","NoPower","NotWorking","ErrorCode","NotLeveled","Loose","Damage","Noise","CustomerCancellation","Missing","TubClean","Cycle/Option","ForeighObjectStuck"]
detail=' '.join(choice(detail_letter) for i in range(TotalSVC))

part_letter=['PCB','Rotor','Stator','DrainPump','Suspension','InletValve','ClutchMotor','NoiseFilter','PowerCord','DrainHose','InnerTub','OuterTub','PressureSensor']
part=' '.join(choice(part_letter) for i in range(TotalSVC))

###report year month
today=date.today()
thisyear=int(today.strftime('%Y'))
letter_year=["2019"]
for i in range(thisyear-2019):
    letter_year.append(str(2020+i))
report_year=' '.join(choice(letter_year) for i in range(TotalSVC))
letter_month=["01","02","03","04","05","06","07","08","09","10","11","12"] # 길이가 같아야 해서 어쩔수 없
report_month=' '.join(choice(letter_month) for i in range(TotalSVC))

#change to list
symptom=symptom.split()
detail=detail.split()
part=part.split()
report_year=report_year.split()
report_month=report_month.split()

#dataframe 생성
svc_data=pd.DataFrame({'Symptoms':symptom,'Detail':detail, 'Part':part, 'Report_Year':report_year,'Report_Month':report_month})

#receipt no, Serial no
for i in range(TotalSVC):
    svc_data.at[i,"RCPT_NO_ORD_NO"]="RNN"+str(randint(10000000,99999999))
    svc_data.at[i,"SERIAL_NO 1"]=str(randint(100,999))+"TN"+str(randint(10000000,99999999))
   

###report date
letter_day=["01","02","03","04","05","06","07","08","09","10","11","12","13","14","15",
            "16","17","18","19","20","21","22","23","24","25","26","27","28"]

#달마다 달라지는 날짜 일수
for i in range(TotalSVC):
    condition=svc_data.at[i,"Report_Month"]
    if condition=='01' or condition=='03' or condition=='05' or condition=='07' or condition=='08' or condition=='10' or condition=='12':
        a=randint(1,31)
        if a<10:
            svc_data.at[i,"Report_Day"]="0"+str(a)
        else:
            svc_data.at[i,"Report_Day"]=str(a)
    elif condition=='04' or condition=='06' or condition=='09' or condition=='11':
        a=randint(1,30)
        if a<10:
            svc_data.at[i,"Report_Day"]="0"+str(a)
        else:
            svc_data.at[i,"Report_Day"]=str(a)
    elif condition=='02':
        today=date.today()-timedelta(days=i*30)
        lunaryear=int(svc_data.at[i,"Report_Year"])%4
        if lunaryear==0:
            a=randint(1,29)
            if a<10:
                svc_data.at[i,"Report_Day"]="0"+str(a)
            else:
                svc_data.at[i,"Report_Day"]=str(a)
        else:
            a=randint(1,28)
            if a<10:
                svc_data.at[i,"Report_Day"]="0"+str(a)
            else:
                svc_data.at[i,"Report_Day"]=str(a)
    else:
        print("Year End Month Error")
    i=i+1


#오늘 이후 날짜 버리기
today=date.today()
today_year=int(today.strftime('%Y'))
today_month=int(today.strftime('%m'))
today_day=int(today.strftime('%d'))

for i in range(TotalSVC):
    thisyear=int(svc_data.at[i,'Report_Year'])
    thismonth=int(svc_data.at[i,'Report_Month'])
    thisday=int(svc_data.at[i,'Report_Day'])
    if thisyear>=today_year:
        if thismonth>today_month:
            svc_data.at[i,'Report_Date']="None"
        elif thismonth==today_month:
            if thisday>today_day:
                svc_data.at[i,'Report_Date']="None"
svc_data=svc_data[svc_data['Report_Date']!='None']


#연도,월,일로 날짜만 만들기
svc_data=svc_data.reset_index()
for i in range(len(svc_data)):
    svc_data.at[i,"Report_Date"]=svc_data.at[i,'Report_Year']+"-"+svc_data.at[i,'Report_Month']+"-"+svc_data.at[i,'Report_Day']


################ YearSVCData
#1년, 월수 구하기
today=date.today()
YearNmonth=pd.DataFrame()
for i in range(12):
    k=today-timedelta(days=30*i)
    YearNmonth.at[i,"Month"]=k.strftime('%Y-%m')

#1년 데이터 소팅하기 -- pivot table 이용하기
YearSVC1M=pd.DataFrame()
YearSVC2M=pd.DataFrame()
YearSVC3M=pd.DataFrame()
YearSVC4M=pd.DataFrame()
YearSVC5M=pd.DataFrame()
YearSVC6M=pd.DataFrame()
YearSVC7M=pd.DataFrame()
YearSVC8M=pd.DataFrame()
YearSVC9M=pd.DataFrame()
YearSVC10M=pd.DataFrame()
YearSVC11M=pd.DataFrame()
YearSVC12M=pd.DataFrame()


YearSVC1M=svc_data[svc_data['Report_Date'].str.contains(YearNmonth.at[0,"Month"])]
YearSVC2M=svc_data[svc_data['Report_Date'].str.contains(YearNmonth.at[1,"Month"])]
YearSVC3M=svc_data[svc_data['Report_Date'].str.contains(YearNmonth.at[2,"Month"])]
YearSVC4M=svc_data[svc_data['Report_Date'].str.contains(YearNmonth.at[3,"Month"])]
YearSVC5M=svc_data[svc_data['Report_Date'].str.contains(YearNmonth.at[4,"Month"])]
YearSVC6M=svc_data[svc_data['Report_Date'].str.contains(YearNmonth.at[5,"Month"])]
YearSVC7M=svc_data[svc_data['Report_Date'].str.contains(YearNmonth.at[6,"Month"])]
YearSVC8M=svc_data[svc_data['Report_Date'].str.contains(YearNmonth.at[7,"Month"])]
YearSVC9M=svc_data[svc_data['Report_Date'].str.contains(YearNmonth.at[8,"Month"])]
YearSVC10M=svc_data[svc_data['Report_Date'].str.contains(YearNmonth.at[9,"Month"])]
YearSVC11M=svc_data[svc_data['Report_Date'].str.contains(YearNmonth.at[10,"Month"])]
YearSVC12M=svc_data[svc_data['Report_Date'].str.contains(YearNmonth.at[11,"Month"])]

YearSVCTotal=pd.concat([YearSVC1M,YearSVC2M,YearSVC3M,YearSVC4M,YearSVC5M,YearSVC6M,
                        YearSVC7M,YearSVC8M,YearSVC9M,YearSVC10M,YearSVC11M,YearSVC12M])
                        
pivot_table = pd.crosstab(index=YearSVCTotal.Report_Day, columns=YearSVCTotal.Report_Month, margins=False)

#Pivot_table 칼럼과 인덱스 정수로 변환
pivot_table.columns=range(0,12)
pivot_table.index=range(0,31)
pivot_table=pivot_table.astype(int)


#YearSVCData 만들기 위해 칼럼 이름 바꾸기
today=date.today()
thisM=int(today.strftime('%m'))
YearSVCData=pivot_table

for i in range(12):
    colM=int(YearSVCData.columns[i])
    if i<thisM: #7월 기준이면 1~7월까지
        YearSVCData=YearSVCData.rename(columns={colM:str(i+12-thisM)}) # int는 숫자 순서대로 배치 되어야 해서
    else:
        YearSVCData=YearSVCData.rename(columns={colM:str(i-thisM)})

# 피봇으로 누락된 nan을 되살리기
YearSVCData=YearSVCData.astype(float)
for i in range(12):
    condition_end=YearNdate.at[i,"Ndate"]
    condition_range=31-condition_end
    if condition_range!=0:
        for j in range(condition_range):
            YearSVCData.at[30-j,str(11-i)]==np.nan # 0부터 시작하는 행렬

#필요없는 svc_data 칼럼 연도,월,일로 데이터 제거
svc_data=svc_data.drop(["index","Report_Year","Report_Month","Report_Day"],axis=1)


################### 지표에 필요한 값들 
# 오늘 날짜,어제 날짜 추출
today=date.today()
to_day=today.strftime('%Y-%m-%d') ##today의 형식을 바꾸겠다, string 변환
yester_day=today-timedelta(days=1)
yester_day=yester_day.strftime('%Y-%m-%d')

# 날짜 해당 svc data 뽑기
today_svc_data=svc_data[svc_data['Report_Date'] == to_day]
yesterday_svc_data=svc_data[svc_data['Report_Date'] == yester_day]

# Today_SVC, Yesterday_SVC 
Increase_SVC=len(today_svc_data)
Today_SVC=len(svc_data)
Yesterday_SVC=Today_SVC-Increase_SVC

# Today_Sales, Yesterday_Sales
today=date.today()
st_date=int(today.strftime('%d'))-1 # 0부터 시작하는 데이터
Increase_Sales=int(YearSalesData.at[st_date,11])
Today_Sales=YearSalesData.sum().sum()
Yesterday_Sales=Today_Sales-Increase_Sales

# YearSVCData, YearSalesData Accumulate to make graph
# 오늘날짜 날리기
today=date.today()
today=int(today.strftime('%d'))
for i in range(31-today):
    YearSVCData.at[30-i,'11']=np.nan
    YearSalesData.at[30-i,11]=np.nan

# 누적 그래프 만들기
YearSVCData=YearSVCData.cumsum()
YearSalesData=YearSalesData.cumsum()

################### 아래는 복사 붙여 넣기 #################################################################

# 인덱스 1부터 맞추기
today_svc_data.index = np.arange(1, len(today_svc_data) + 1)

# New Services
n=1
New_Services=""
while n <= len(today_svc_data):
    New_Services=New_Services + str(n) +") "+str(today_svc_data["Symptoms"][n])+"\n   "+str(today_svc_data["RCPT_NO_ORD_NO"][n])+" /// "+str(today_svc_data["SERIAL_NO 1"][n])+"\n"
    n=n+1

########### SVC 만들기 ##############
# SVC Text
SVC="Service Status : "+ str(Yesterday_SVC) + " → " + str(Today_SVC) +" ("+str(Increase_SVC)+"↑)"

########### Week 추출하기 #######
year, week_num, day_of_week=date.today().isocalendar()
week_num=week_num+11
Weeks='W'+str(week_num)

########### Today, Yesterday Sales 만들기 #################
#Sales Text
Sales="Sales Status : "+ str(int(Yesterday_Sales)) + " → " + str(int(Today_Sales)) +" ("+str(int(Today_Sales-Yesterday_Sales))+"↑)"

####################### FDR 만들기 #####################
Today_FDR=round(Today_SVC*100/Today_Sales,2)
Yesterday_FDR=round(Yesterday_SVC*100/Yesterday_Sales,2)


###################### Target 만들기 ###############################
##random 데이터 생성
Target=Today_FDR+randint(1,10)/100

# FDR status 추출
FDR="FDR Status : "+str(Yesterday_FDR)+  " → " + str(Today_FDR) + " % ("+str(Weeks)+" Target "+str(round(Target,2))+"%)"


#################### 문자열 에러 체크하기
# print(SVC)
# print(Sales)
# print(FDR)

#################### Pivot chart 만들기 ###############################

ea= svc_data["Symptoms"].value_counts(dropna=True,sort=True).to_frame()
ea.columns=["EA"]
total=pd.DataFrame([Today_SVC])
total.columns=["EA"]
total.index=["TOTAL"]
ea=pd.concat([ea,total],axis=0)


ppm=pd.DataFrame()
ppm["PPM"]=round(ea["EA"]*1000000/TotalProd,0)
ppm=ppm.astype(int)

#table 합
Table=pd.concat([ea,ppm],axis=1)
Plabels=Table.index[:-1].to_list()
Pvalues=Table['PPM'][:-1].to_list() #total 제외


##########################그래프 만들기 1번째 축
# 데이터 레이블 이름 완성하기


today=date.today()
date0M_name=today.strftime('%Y.%m')
date1M_name=today-timedelta(weeks=4) # 어떤 달은 한달이 4주가 아닌 점을 고려
date1M_name=date1M_name.strftime('%Y.%m')
date2M_name=today-timedelta(weeks=8) # 어떤 달은 한달이 4주가 아닌 점을 고려
date2M_name=date2M_name.strftime('%Y.%m')
# 그래프 그리기 위해 데이터 합치기
SVCresult=YearSVCData[['9','10','11']] 
SVCresult.columns=['SVC_'+date2M_name,'SVC_'+date1M_name,'SVC_'+date0M_name]
Salesresult=YearSalesData[[9,10,11]] # 최근 삼개월 데이터 추출
Salesresult.columns=['Sales_'+date2M_name,'Sales_'+date1M_name,'Sales_'+date0M_name]

# app.py move variable
legend2M=date2M_name
legend1M=date1M_name
legend0M=date0M_name

ABlabels=list(range(1,len(Salesresult.index)+1))

# zero not display
Avalues2M=SVCresult['SVC_'+date2M_name].dropna().to_list()
Avalues1M=SVCresult['SVC_'+date1M_name].dropna().to_list()
Avalues0M=SVCresult['SVC_'+date0M_name].dropna().to_list()

Bvalues2M=Salesresult['Sales_'+date2M_name].fillna(0).to_list()
Bvalues1M=Salesresult['Sales_'+date1M_name].fillna(0).to_list()
Bvalues0M=Salesresult['Sales_'+date0M_name].fillna(0).to_list()


svc_data.index=range(1,len(svc_data)+1)
svc_data.columns=["Symptom","Details","Parts", "Repair_No","Serial_No","Report_Date"]

min_svc_data=svc_data.loc[svc_data['Report_Date'].str.contains(legend0M)]
min_svc_data.index=range(1,len(min_svc_data)+1)

svc_data_html=svc_data.to_html()
svc_data_html=svc_data_html.replace('border="1" class="dataframe"','id="datatablesSimple"' )
svc_data_html=svc_data_html.replace('<tr style="text-align: right;">','<tr>')
svc_data_html=svc_data_html.replace('<th></th>','<th>No</th>')

min_data_html=min_svc_data.to_html()
min_data_html=min_data_html.replace('border="1" class="dataframe"','id="datatablesSimple"' )
min_data_html=min_data_html.replace('<tr style="text-align: right;">','<tr>')
min_data_html=min_data_html.replace('<th></th>','<th>No</th>')