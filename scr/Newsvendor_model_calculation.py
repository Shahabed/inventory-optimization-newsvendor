# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 13:02:52 2023

@author: S.C.Azizabadi
"""

import pandas as pd
import sqlalchemy
import datetime
import time



#Kosten nur für AS
# c_u = 0.6524 
# c_o = 0.105
# critical = (c_u / (c_o+c_u))

#Kosten AS+Grosso
#Was für überbelieferungskosten hat Grosso
c_u = 0.8679 - 0.105
c_o = 0.105 - 0.001254
critical = (c_u / (c_o+c_u))

def calc_newsvendor(Demand):
    """calculates the empirical CDF for a Demand Timeseries and returns the optimal quantity.
    calculates the newsvendor model for a given Demand timeseries, with the critical ratio 'critical'"""
    P = Demand.value_counts() / Demand.shape[0]
    CDF = P.sort_index().cumsum()
    opt_Q = CDF[CDF >= critical ].index.min()  
    return opt_Q
#%% Newsvendor for complete OGR  ~30min
def newsvendor_complete():
    """Return the optimal quantities for every shop and every weekday for OGR = 7"""
    #load data
    print(f'start {datetime.datetime.today()}')
    conn  = sqlalchemy.create_engine('...', fast_executemany=True)
    sql = f'''select VK.EH_KEY, VK.OBJ_KEY, VK.KALWT, (VK.BEZUG-VK.REMI) as VERKAUF,  LS.EV as EV from ablage.eh.tb_verkauf_mars AS VK 
    LEFT JOIN (SELECT a.[EH_KEY]
      ,a.[OBJ_KEY]
      ,a.[EVT]
      ,a.[EV]
      ,a.[TIMESTAMP]
  FROM [Regulierungsstatistik].[dbo].[TB_MO_LOST_SALES] as a
    inner join 
        (SELECT [EH_KEY]
      ,[OBJ_KEY]
      ,[EVT]
      ,MAX([TIMESTAMP]) as MAXTIME
  FROM [Regulierungsstatistik].[dbo].[TB_MO_LOST_SALES] GROUP BY EH_KEY, OBJ_KEY, EVT) as b on
        a.TIMESTAMP = b.MAXTIME and a.EH_KEY = b.EH_KEY and a.OBJ_KEY = b.OBJ_KEY and a.EVT = b.EVT) as LS ON VK.EH_KEY = LS.EH_KEY and VK.OBJ_KEY = LS.OBJ_KEY and VK.EVT = (YEAR(LS.EVT)*10000 + MONTH(LS.EVT)*100 + DAY(LS.EVT)) 
    where VK.EVT >= 20220101 and VK.OGR_KEY = 7 ''' 
    DF = pd.read_sql(sql, conn)
    print(f'SQL finished {datetime.datetime.today()}')
    #replace NaNs with 0, so calc_newsvendor won't produce NaNs
    DF['EV'].fillna(0, inplace = True)
    #create Demand
    DF['D'] = DF['VERKAUF'] + DF['EV']
    DF.D = DF.D.round(0)
    #apply calc_newsvendor function on every groupby element
    DF = DF.groupby([ 'OBJ_KEY', 'EH_KEY', 'KALWT'], group_keys=False).D.apply(calc_newsvendor)
    print(f'Calculation finished {datetime.datetime.today()}')
    return DF

start = time.time()
NV = newsvendor_complete()
print('It took', time.time()-start, 'seconds.')


#below are other version for different aggregation levels

#%% Newsvendor per Grosso fil
def newsvendor_grossofil_complete(HKDFIL2_KEY):
    print(f'start {datetime.datetime.today()}')
    conn  = sqlalchemy.create_engine('...', fast_executemany=True)
    sql = f'''select VK.EH_KEY, VK.OBJ_KEY, VK.KALWT, (VK.BEZUG-VK.REMI) as VERKAUF,  LS.EV as EV from ablage.eh.tb_verkauf_mars AS VK LEFT JOIN [ANWENDUNG].[kpi].[TB_EH_S] AS HKD ON VK.EH_KEY = HKD.EH_KEY
    LEFT JOIN [Regulierungsstatistik].[dbo].[TB_MO_LOST_SALES] as LS ON VK.EH_KEY = LS.EH_KEY and VK.OBJ_KEY = LS.OBJ_KEY and VK.EVT = (YEAR(LS.EVT)*10000 + MONTH(LS.EVT)*100 + DAY(LS.EVT)) 
    where VK.EVT >= 20220101 and VK.OGR_KEY = 7 and HKD.HKDFIL2_KEY = {HKDFIL2_KEY} ''' #and VK.KALWT = {WD}
    DF = pd.read_sql(sql, conn)
    print(f'SQL finished {datetime.datetime.today()}')
    DF['EV'].fillna(0, inplace = True)
    DF['D'] = DF['VERKAUF'] + DF['EV']
    DF.D = DF.D.round(0)
    DF = DF.groupby([ 'OBJ_KEY', 'EH_KEY', 'KALWT'], group_keys=False).D.apply(calc_newsvendor)
    print(f'Calculation finished {datetime.datetime.today()}')
    return DF

start = time.time()
dic = {}
for fil in [45501,45502,45503]:
    res_complete_grossofil = newsvendor_grossofil_complete(fil)
    dic[fil] = res_complete_grossofil
print('It took', time.time()-start, 'seconds.')


#%% Newsvendor per Grosso, faster than per Grosso fil
def newsvendor_grossofil_complete(HKD):
    print(f'start {datetime.datetime.today()}')
    conn  = sqlalchemy.create_engine('...', fast_executemany=True)
    sql = f'''select VK.EH_KEY, VK.OBJ_KEY, VK.KALWT, (VK.BEZUG-VK.REMI) as VERKAUF,  LS.EV as EV from ablage.eh.tb_verkauf_mars AS VK LEFT JOIN [ANWENDUNG].[kpi].[TB_EH_S] AS HKD ON VK.EH_KEY = HKD.EH_KEY
    LEFT JOIN [Regulierungsstatistik].[dbo].[TB_MO_LOST_SALES] as LS ON VK.EH_KEY = LS.EH_KEY and VK.OBJ_KEY = LS.OBJ_KEY and VK.EVT = (YEAR(LS.EVT)*10000 + MONTH(LS.EVT)*100 + DAY(LS.EVT)) 
    where VK.EVT >= 20220101 and VK.OGR_KEY = 7 and HKD.HKD_KEY = {HKD} ''' #and VK.KALWT = {WD}
    DF = pd.read_sql(sql, conn)
    print(f'SQL finished {datetime.datetime.today()}')
    DF['EV'].fillna(0, inplace = True)
    DF['D'] = DF['VERKAUF'] + DF['EV']
    DF.D = DF.D.round(0)
    DF = DF.groupby([ 'OBJ_KEY', 'EH_KEY', 'KALWT'], group_keys=False).D.apply(calc_newsvendor)
    print(f'Calculation finished {datetime.datetime.today()}')
    return DF

start = time.time()
Test_complete_grosso = newsvendor_grossofil_complete(455)
print('It took', time.time()-start, 'seconds.')








#%%compare current costs against NV costs
def compare(NV_RES):
    conn  = sqlalchemy.create_engine('...', fast_executemany=True)
    sql = f'''select VK.EH_KEY, VK.OBJ_KEY, VK.KALWT,VK.BEZUG,  (VK.BEZUG-VK.REMI) as VERKAUF,  LS.EV as EV from ablage.eh.tb_verkauf_mars AS VK LEFT JOIN [ANWENDUNG].[kpi].[TB_EH_S] AS HKD ON VK.EH_KEY = HKD.EH_KEY
    LEFT JOIN [Regulierungsstatistik].[dbo].[TB_MO_LOST_SALES] as LS ON VK.EH_KEY = LS.EH_KEY and VK.OBJ_KEY = LS.OBJ_KEY and VK.EVT = (YEAR(LS.EVT)*10000 + MONTH(LS.EVT)*100 + DAY(LS.EVT)) 
    where VK.EVT >= 20220101 and VK.EVT < 20230101 and VK.OGR_KEY = 7 ''' 
    DF = pd.read_sql(sql, conn)
    DF['EV'].fillna(0, inplace = True)
    DF['D'] = DF['VERKAUF'] + DF['EV']
    DF.D = DF.D.round(0)   
    NV_RES = NV_RES.reset_index().rename(columns = {'D' : 'Q_OPT'})    
    DF = DF.merge(NV_RES, on = ['OBJ_KEY', 'EH_KEY', 'KALWT'], how = 'left')   
    DF.loc[DF.BEZUG > DF.D, 'cost'] = (DF.BEZUG - DF.D) * c_o
    DF.loc[DF.BEZUG <= DF.D, 'cost'] = (DF.D - DF.BEZUG) * c_u   
    DF.loc[DF.Q_OPT > DF.D, 'cost_NV'] = (DF.Q_OPT - DF.D) * c_o
    DF.loc[DF.Q_OPT <= DF.D, 'cost_NV'] = (DF.D - DF.Q_OPT) * c_u
    print(f'Kosten normale dispo: {DF.cost.sum()}')
    print(f'Kosten NV dispo:      {DF.cost_NV.sum()}')

#%% Newsvendor per Grossofil and Weekday, slower than Newsvendor per Grossofil
def newsvendor_grosso_weekday(HKDFIL2_KEY, WD):
    print(f'start {datetime.datetime.today()}')
    conn  = sqlalchemy.create_engine('...', fast_executemany=True)
    sql = f'''select VK.EH_KEY, VK.OBJ_KEY, (VK.BEZUG-VK.REMI) as VERKAUF,  LS.EV as EV from ablage.eh.tb_verkauf_mars AS VK LEFT JOIN [ANWENDUNG].[kpi].[TB_EH_S] AS HKD ON VK.EH_KEY = HKD.EH_KEY
    LEFT JOIN [Regulierungsstatistik].[dbo].[TB_MO_LOST_SALES] as LS ON VK.EH_KEY = LS.EH_KEY and VK.OBJ_KEY = LS.OBJ_KEY and VK.EVT = (YEAR(LS.EVT)*10000 + MONTH(LS.EVT)*100 + DAY(LS.EVT)) 
    where VK.EVT >= 20210101 and VK.EVT < 20220101 and VK.OGR_KEY = 7 and HKD.HKDFIL2_KEY = {HKDFIL2_KEY} and VK.KALWT = {WD} ''' 
    DF = pd.read_sql(sql, conn)
    print(f'SQL finished {datetime.datetime.today()}')
    DF['EV'].fillna(0, inplace = True)
    DF['D'] = DF['VERKAUF'] + DF['EV']
    DF.D = DF.D.round(0)
    DF = DF.groupby([ 'OBJ_KEY', 'EH_KEY'], group_keys=False).D.apply(calc_newsvendor)
    print(f'Calculation finished {datetime.datetime.today()}')
    return DF
#%% Newsvendor per Grossofil and Weekday, slower than Newsvendor per Grossofil
def newsvendor_grosso_weekday(HKDFIL2_KEY, WD):
    print(f'start {datetime.datetime.today()}')
    conn  = sqlalchemy.create_engine('...', fast_executemany=True)
    sql = f'''select VK.EH_KEY, VK.OBJ_KEY, (VK.BEZUG-VK.REMI) as VERKAUF,  LS.EV as EV from ablage.eh.tb_verkauf_mars AS VK LEFT JOIN [ANWENDUNG].[kpi].[TB_EH_S] AS HKD ON VK.EH_KEY = HKD.EH_KEY
    LEFT JOIN (SELECT a.[EH_KEY]
      ,a.[OBJ_KEY]
      ,a.[EVT]
      ,a.[EV]
      ,a.[TIMESTAMP]
  FROM [Regulierungsstatistik].[dbo].[TB_MO_LOST_SALES] as a
    inner join 
        (SELECT [EH_KEY]
      ,[OBJ_KEY]
      ,[EVT]
      ,MAX([TIMESTAMP]) as MAXTIME
  FROM [Regulierungsstatistik].[dbo].[TB_MO_LOST_SALES] GROUP BY EH_KEY, OBJ_KEY, EVT) as b on
        a.TIMESTAMP = b.MAXTIME and a.EH_KEY = b.EH_KEY and a.OBJ_KEY = b.OBJ_KEY and a.EVT = b.EVT) as LS ON VK.EH_KEY = LS.EH_KEY and VK.OBJ_KEY = LS.OBJ_KEY and VK.EVT = (YEAR(LS.EVT)*10000 + MONTH(LS.EVT)*100 + DAY(LS.EVT)) 
    where VK.EVT >= 20210101 and VK.EVT < 20220101 and VK.OGR_KEY = 7 and HKD.HKDFIL2_KEY = {HKDFIL2_KEY} and VK.KALWT = {WD} ''' 
    DF = pd.read_sql(sql, conn)
    print(f'SQL finished {datetime.datetime.today()}')
    DF['EV'].fillna(0, inplace = True)
    DF['D'] = DF['VERKAUF'] + DF['EV']
    DF.D = DF.D.round(0)
    DF = DF.groupby([ 'OBJ_KEY', 'EH_KEY'], group_keys=False).D.apply(calc_newsvendor)
    print(f'Calculation finished {datetime.datetime.today()}')
    return DF

#Kosten nur für AS
c_u = 0.6524 
c_o = 0.105
critical = (c_u / (c_o+c_u))


start = time.time()
RES_AS = newsvendor_grosso_weekday(45501, 1)
print('It took', time.time()-start, 'seconds.')  

#Kosten AS+Grosso
#Was für überbelieferungskosten hat Grosso
c_u = 0.8679 - 0.105
c_o = 0.105 - 0.001254
critical = (c_u / (c_o+c_u))
start = time.time()

RES_AS_GROSSO = newsvendor_grosso_weekday(45501, 1)

print('It took', time.time()-start, 'seconds.')    


RES_COMP = RES_AS.reset_index().rename(columns = {'D': 'Q_OPT_AS'}).merge(RES_AS_GROSSO.reset_index().rename(columns = {'D':'Q_OPT_AS_GROSSO'}), on = ['EH_KEY', 'OBJ_KEY'], how = 'left')
RES_COMP.Q_OPT_AS.sum() - RES_COMP.Q_OPT_AS_GROSSO.sum()
RES_COMP.Q_OPT_AS.sum()

