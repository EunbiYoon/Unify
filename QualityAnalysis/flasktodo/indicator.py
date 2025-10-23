## random dataframe 생성
from random import *
import pandas as pd
from datetime import datetime
import numpy as np
import pandas as pd
from dateutil import relativedelta

##### 올해 몇월인지 구하기
Today_Year=int(datetime.today().year)
Today_Month=int(datetime.today().month)

month_data=pd.DataFrame()
##### 지난 달 구하기
for i in range(Today_Year-2019+1): #마지막 숫자는 포함 안됨으로
    if i+2019==Today_Year:
        for j in range(Today_Month): #올해
            month_data.at[12*i+j,"month"]=str(19+i)+"."+str(j+1) #달은 1부터 시작
    else:
        for j in range(12): #나머지 해
            month_data.at[12*i+j,"month"]=str(19+i)+"."+str(j+1) #달은 1부터 시작

##### 달 수가 4자리 인경우 가운데 0을 채워 넣기
for i in range(len(month_data)):
    month_condition=month_data.at[i,"month"]
    if len(str(month_condition))==4:
        month_data.at[i,"month"]=month_condition[:3]+"0"+month_condition[3:]
    else:
        pass

##### list로 바꾸기 (Series -> list)
month_list=month_data["month"].tolist()


########## random data 만들기 ####################
#Model
def random_function():
    letter1=["WT7100","WT7300","WT7405","WT7800"]
    model=' '.join(choice(letter1) for i in range(3000))

    #Symptom
    letter2=["DRAIN","EXPLANATION","EXTERIOR","FILLING","LEAK","LID","MISASSEMBLY","MOTOR","NOISE/VIBRATION","OTHER","PCB","RETURN"]
    symptom=' '.join(choice(letter2) for i in range(3000))

    #SVC Date
    svcdate=' '.join(choice(month_list) for i in range(3000))
    
    #Production Date
    prodate=' '.join(choice(month_list) for i in range(3000))

    #change to list
    model=model.split()
    symptom=symptom.split()
    svcdate=svcdate.split()
    prodate=prodate.split()

    #change to dataframe
    svc_data=pd.DataFrame({'Model':model,'Symptoms':symptom,'GQISClosingMonth':svcdate,'ProductionMonth':prodate})

    #Prod >= SVC date
    svc_data=svc_data[svc_data['GQISClosingMonth']>=svc_data['ProductionMonth']]

    #SVC data >= todayMonth
    today = datetime.today()
    todayMonth=today.strftime('%y%m')
    svc_data=svc_data[svc_data['GQISClosingMonth']<=todayMonth]
    svc_data.reset_index(inplace=True, drop=True)

    today = datetime.today()
    today=today.strftime('%Y/%m/%d')

    dateformat = '%Y/%m/%d'
    startDate  = datetime.strptime('2019/01/01',dateformat).date()
    endDate = datetime.strptime(today,dateformat).date()
    date_diff = relativedelta.relativedelta(endDate,startDate)
    nowMonth=int(date_diff.months)+1+int(date_diff.years)*12

    #nowMonth 있으니 Production Qty랜덤 데이터 추출
    randP=list(range(1000,3000))
    MonthP=' '.join(str(choice(randP)) for i in range(nowMonth))

    #nowMonth 있으니 Sales Qty랜덤 데이터 추출
    randS=list(range(1000,3000))
    MonthS=' '.join(str(choice(randS)) for i in range(nowMonth))

    #MonthP, MonthS를 리스트로 변환
    MonthP=MonthP.split()
    MonthS=MonthS.split()

    #change to dataframe
    PSQty=pd.DataFrame({'Production Qty':MonthP,'Sales Qty':MonthS})
    PSQty=PSQty.T
    PROD_data=PSQty.loc['Production Qty']
    SALES_data=PSQty.loc['Sales Qty']

    #데이터 안의 값들을 int로 변환
    PROD_data=PROD_data.astype(int)
    SALES_data=SALES_data.astype(int)

    return svc_data, PROD_data, SALES_data


################################# 데이터의 기본인 Pivot table 만들기 ###############################    
def basic_function(input_data):
    svc_data=random_function()[0]
    for i in range(len(input_data)):
        a=input_data[i]
        for j in range(len(svc_data)):
            b=svc_data.at[j,'Symptoms']
            if b==a:
                svc_data.at[j,'Sort']=True
            else:
                False
    #sort data 정리
    sort_data=svc_data.dropna()
    sort_data.reset_index(inplace=True, drop=True)
    sort_data=sort_data.drop(['Sort'],axis=1)

    pivot_table = pd.crosstab(index=sort_data.GQISClosingMonth, columns=sort_data.ProductionMonth, margins=True, margins_name="Total")
    idx2 = pivot_table.columns.union(pivot_table.index) # 가로 세로 동일한 index
    pyramid_table = pivot_table.reindex(index = idx2, columns=idx2, fill_value=0)

    ## pyramid_table의 value 추출, tranpose 행렬 A^T in list
    var = [ ]
    for column in pyramid_table.columns.values:
        var.append ( pyramid_table [ column ].tolist () )
    numpy_array = np.array(var)
    transpose = numpy_array.T
    pyramid_vals = transpose.tolist()
    return pyramid_vals, pyramid_table, idx2, pivot_table


def pivot_function(input_data):
    pyramid_table=basic_function(input_data)[1]
    #값이 0이면 데이터 값 없애기 -> 너무 많은 0을 제거
    pyramid_table = pyramid_table.replace(0,'', regex=True)
    
    return pyramid_table
    
def hazard_function(input_data):
    pyramid_vals=basic_function(input_data)[0]
    idx2=basic_function(input_data)[2]
    PROD_data=random_function()[1]
    pyramid_vals.pop(len(pyramid_vals)-1)
    pyramid_vals=pd.DataFrame(pyramid_vals)
    pyramid_vals= pyramid_vals [pyramid_vals.columns [:-1]]
    pyramid_vals.drop(columns=[len(pyramid_vals)-1])

    #a의 원소들을 모두 int형으로 변환
    A=pyramid_vals.apply(pd.to_numeric)

    ## Hazard 그래프 그리기 시작
    ## 삼각행렬을 위로 올리기
    b=pd.DataFrame()
    i=0
    j=0
    for i in range(len(A)):
        for j in range(len(A)):
            if i==j:
                k=A.at[i,j]
                b.at[0,j]=k
                j=j+1
            elif i>j:
                k=A.at[i,j]
                b.at[i-j,j]=k
                j=j+1

    #### 삼각행렬 누적 더하기
    b=b.replace(np.nan,0, regex=True)
    c=pd.DataFrame()

    #첫번쨰 열 처리
    for i in range(1):
        for j in range(len(A)):
            k=b.at[0,j]
            c.at[0,j]=k

    # 두번째 열 처리 -> 첫번쨰 시작하는 열은 1번째인데 i가 0부터 인식함으로 i+1로 식을 전개
    for i in range(len(A)-1):
        for j in range(len(A)-i-1):
            M=b.at[i+1,j]
            N=c.at[i,j]
            c.at[i+1,j]=M+N              
   
    # Hazard 그래프 전 마지막 테이블
    hazard_table=pd.DataFrame()
    i=0
    j=0
    for i in range(len(idx2)-1): # idx에 total도 포함되어 있다.
        for j in range(len(idx2)-1):
            d=c.at[i,j]
            if d==np.nan:
                hazard_table.at[i,j]=np.nan
            else:
                e=int(PROD_data.loc[j])
                if e==0:
                    k=0
                else:
                    k=d*100/e
                hazard_table.at[i,j]=round(k,2)
                j=j+1
    return hazard_table
    

def ppm_function(input_data):
    pyramid_vals=basic_function(input_data)[0]
    PROD_data=random_function()[1]

    pyramid_vals.pop(len(pyramid_vals)-1)
    pyramid_vals=pd.DataFrame(pyramid_vals)
    pyramid_vals= pyramid_vals [pyramid_vals.columns [:-1]]
    pyramid_vals.drop(columns=[len(pyramid_vals)-1])

    #a의 원소들을 모두 int형으로 변환
    A=pyramid_vals.apply(pd.to_numeric)

    # print("How many months ago was it improved? [(ex)Improvement Month :2103, last production closing Month: 2106 --> input : 3 ")
    # improving_month=input()
    # print("Improving Month: "+improving_month)
    improving_month=3

    #AAR개선전
    i=0
    j=0
    k=0
    n=int(improving_month)
    for i in range(n):
        for j in range(n):
            k=A.at[len(A)-i-1-n,len(A)-j-1-n]+k
            j=j+1
    before_ImprovSVC=k

    #AAR개선후
    i=0
    j=0
    k=0
    for i in range(n):
        for j in range(n):
            k=A.at[len(A)-i-1,len(A)-j-1]+k
            j=j+1
    after_ImprovSVC=k


    ##Prod Qty 개선전
    i=0
    k=0
    n=int(improving_month)
    for i in range(n):
        k=int(PROD_data.loc[len(PROD_data)-i-1-n])+k
        i=i+1
    before_ProdQty=int(k)

    ##Prod Qty 개선후
    i=0
    k=0
    for i in range(n):
        k=int(PROD_data.loc[len(PROD_data)-i-1])+k
        i=i+1
    after_ProdQty=int(k)

    ##AAR PPM dataframe 생성하고 값 배치
    ARPMdata=pd.DataFrame()
    ARPMdata.at[1,1]=str(before_ImprovSVC)+' ea'
    ARPMdata.at[1,2]=str(after_ImprovSVC)+' ea'
    ARPMdata.at[2,1]=str(before_ProdQty)+' ea'
    ARPMdata.at[2,2]=str(after_ProdQty)+' ea'

    ##PPM
    ARPMdata.at[3,1]=str(round(before_ImprovSVC*1000000/before_ProdQty,2))+' ppm'
    before_AAR=round(before_ImprovSVC*1000000/before_ProdQty,2) # 최종 개선율 구하기 위해

    ARPMdata.at[3,2]=str(round(after_ImprovSVC*1000000/after_ProdQty,2))+' ppm'
    after_AAR=round(after_ImprovSVC*1000000/after_ProdQty,2)# 최종 개선율 구하기 위해

    ##AAR
    ARPMdata.at[4,1]=""
    if before_AAR==0:
        ARPMdata.at[4,2]="Divide by zero"
    else:
        ARPMdata.at[4,2]=str(round((before_AAR-after_AAR)*100/before_AAR,2))+' %'

    ##칼럼 인덱스 이름 바꾸기
    ARPMdata.columns = ["Before Improvement", "After Improvement"]
    ARPMdata.index = ["SVC", "Production Qty","PPM","AAR"]

    ###matplotlib table value 생성
    ARPMdata_var = [ ]
    for column in ARPMdata.columns.values:
        ARPMdata_var.append ( ARPMdata [ column ].tolist () )
    ARPMdata_numpy_array = np.array(ARPMdata_var)
    ARPMdata_transpose = ARPMdata_numpy_array.T
    ARPMdata_transpose_list = ARPMdata_transpose.tolist()
    ARPMdata_table_vals=ARPMdata_transpose_list
    return ARPMdata


def ffr_function(input_data):
    pyramid_table=basic_function(input_data)[1]
    idx2=basic_function(input_data)[2]
    SALES_data=random_function()[2]

    ## L12_SVC, L12_Sales, Weight_Sales dataframe
    L12_SVC = pd.DataFrame(index=range(0,len(idx2)-1),columns=['L12_SVC']) # total 까지 포함한 값
    L12_Sales = pd.DataFrame(index=range(0,len(idx2)-1),columns=['L12_Sales'])
    Weight_Sales = pd.DataFrame()
    FDR = pd.DataFrame(index=range(0,len(idx2)-1),columns=['FDR'])
    FFR = pd.DataFrame(index=range(0,len(idx2)-1),columns=['FFR'])

    # 반복문을 위해 index를 셋팅
    SVC_table=pyramid_table.reset_index()
    SVC_table=SVC_table.drop('index',axis=1)
    SVC_table=SVC_table.T
    SVC_table=SVC_table.reset_index()
    SVC_table=SVC_table.drop('index',axis=1)


    #####################################################
    ##### L12 SVC 만들기
    i=0
    k=0
    j=0
    t=-1

    for i in range(len(idx2)-1):
        if i<12:
            k=0
            for t in range(i):
                for j in range(i):
                    k=SVC_table.at[i-t,i-j]+k
                    j=j+1
        else:
            k=0
            for t in range(12):
                for j in range(12):
                    k=SVC_table.at[i-t,i-j]+k
                    j=j+1
        L12_SVC.at[i,'L12_SVC']=k
        i=i+1

    #####################################################

    # Accumulate Sale
    Acc=SALES_data.cumsum()
    Acc=Acc.reset_index()
    Acc=Acc.drop(['index'],axis=1)
    Acc.columns=['Acc']



    # Accumulate 한 것 빼기
    k=0
    for i in range(len(idx2)-1):
        if i<12:
            k=Acc.at[i,'Acc']
        else:
            k=int(Acc.at[i,'Acc'])-int(Acc.at[i-12,'Acc'])
        L12_Sales.at[i,'L12_Sales']=k
        i=i+1

    #####################################################
    ##### Weight Sales 만들기
    for i in range(len(idx2)-1):
        if i<12:
            j=0
            k=0
            for j in range(i+1):
                k=int(SALES_data.loc[j])*(i+1-j)/12+k
                Weight_Sales.at[i,'Weight_Sales']=k
                j=j+1
        else:
            k=0
            for t in range(12):
                k=int(SALES_data.at[t+i-11])*(12-t)/12+k
                t=t+1
        Weight_Sales.at[i,'Weight_Sales']=k
        i=i+1



    #####################################################
    ##### FDR 만들기
    condition=0
    for i in range(len(idx2)-1):
        condition=L12_Sales.at[i,'L12_Sales']
        if condition==0:
            #np.nan
            FDR.at[i,'FDR']=0
        else:
            FDR.at[i,'FDR']=int(L12_SVC.at[i,'L12_SVC'])*100/int(L12_Sales.at[i,'L12_Sales'])
        i=i+1

    #####################################################
    ##### FFR 만들기
    condition=0
    for i in range(len(idx2)-1):
        condition=Weight_Sales.at[i,'Weight_Sales']
        if condition==0:
            FFR.at[i,'FFR']=0
        else:
            FFR.at[i,'FFR']=L12_SVC.at[i,'L12_SVC']*100/Weight_Sales.at[i,'Weight_Sales']
        i=i+1

    fdrffr=pd.concat([FDR,FFR],axis=1)
    fdrffr=fdrffr.astype(float)
    fdrffr=fdrffr.round(2)# 소숫점 둘째 자리

    today=datetime.today()
    thisyear_cutoff=int(today.strftime("%m"))

    FDR_1Y=pd.DataFrame()
    FFR_1Y=pd.DataFrame()

    FDR_2Y=pd.DataFrame()
    FFR_2Y=pd.DataFrame()

    FDR_3Y=pd.DataFrame()
    FFR_3Y=pd.DataFrame()

    FDR_4Y=pd.DataFrame()
    FFR_4Y=pd.DataFrame()


    ###################### 어차피 데이터는 3개년 2019 부터 시작
    # 일단 행렬에 넣고
    for i in range(len(idx2)-1): # Total 제
        if i<12:
            FDR_1Y.at[i,'FDR_1Y']=fdrffr.at[len(idx2)-2-i,'FDR'] # Total, 0 부터 숫자 세기 시작함
            FFR_1Y.at[i,'FFR_1Y']=fdrffr.at[len(idx2)-2-i,'FFR']
        elif i<24:
            FDR_2Y.at[i,'FDR_2Y']=fdrffr.at[len(idx2)-2-i,'FDR']
            FFR_2Y.at[i,'FFR_2Y']=fdrffr.at[len(idx2)-2-i,'FFR']
        elif i<36:
            FDR_3Y.at[i,'FDR_3Y']=fdrffr.at[len(idx2)-2-i,'FDR']
            FFR_3Y.at[i,'FFR_3Y']=fdrffr.at[len(idx2)-2-i,'FFR']
        elif i<48:
            FDR_4Y.at[i,'FDR_4Y']=fdrffr.at[len(idx2)-2-i,'FDR']
            FFR_4Y.at[i,'FFR_4Y']=fdrffr.at[len(idx2)-2-i,'FFR']
        elif i<60:
            FDR_4Y.at[i,'FDR_5Y']=fdrffr.at[len(idx2)-2-i,'FDR']
            FFR_4Y.at[i,'FFR_5Y']=fdrffr.at[len(idx2)-2-i,'FFR']

        else:
            print("done!")


    FFR1YValues=FFR_1Y['FFR_1Y'].dropna().to_list()
    FFR2YValues=FFR_2Y['FFR_2Y'].dropna().to_list()
    FFR3YValues=FFR_3Y['FFR_3Y'].dropna().to_list()
    FFR4YValues=FFR_4Y['FFR_4Y'].dropna().to_list()

    FDR1YValues=FDR_1Y['FDR_1Y'].dropna().to_list()
    FDR2YValues=FDR_2Y['FDR_2Y'].dropna().to_list()
    FDR3YValues=FDR_3Y['FDR_3Y'].dropna().to_list()
    FDR4YValues=FDR_4Y['FDR_4Y'].dropna().to_list()

    FFR1YLegend="FFR Last 1 Years"
    FFR2YLegend="FFR Last 2 Years"
    FFR3YLegend="FFR Last 3 Years"
    FFR4YLegend="FFR Last 4 Years"

    FDR1YLegend="FDR Last 1 Years"
    FDR2YLegend="FDR Last 2 Years"
    FDR3YLegend="FDR Last 3 Years"
    FDR4YLegend="FDR Last 4 Years"

    return FFR1YValues,FFR1YLegend,FDR1YValues,FDR1YLegend,FFR2YValues,FFR2YLegend,FDR2YValues,FDR2YLegend,FFR3YValues,FFR3YLegend,FDR3YValues,FDR3YLegend,FFR4YValues,FFR4YLegend,FDR4YValues,FDR4YLegend

   

    