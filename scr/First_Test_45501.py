# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 13:36:52 2023

@author: S.C.Azizabadi
"""
import pandas as pd
import sqlalchemy
import datetime
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
def newsvendor_complete(shops):
    """Return the optimal quantities for every shop and every weekday for OGR = 7"""
    #load data
    print(f'start {datetime.datetime.today()}')
    conn  = sqlalchemy.create_engine('mssql://deaxsmapsql01.itservices.asudc.net,6200/Regulierungsstatistik?trusted_connection=yes&driver=SQL+Server', fast_executemany=True)
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
    where VK.EVT >= 20220101 and VK.OGR_KEY = 7 and VK.EH_KEY in {shops}''' 
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

#%% identify 50 worst shops
HKDFIL = 45501
dat1 = 20220101
dat2 = 20230301
def get_worst50shops(HKDFIL,dat1, dat2):
    conn  = sqlalchemy.create_engine('mssql://deaxsmapsql01.itservices.asudc.net,6200/Regulierungsstatistik?trusted_connection=yes&driver=SQL+Server', fast_executemany=True)
    sql = f'''select VK.EH_KEY, VK.EVT, VK.OBJ_KEY, VK.KALWT, (VK.BEZUG-VK.REMI) as VERKAUF, VK.BEZUG,  LS.EV as EV from ablage.eh.tb_verkauf_mars AS VK LEFT JOIN [ANWENDUNG].[kpi].[TB_EH_S] AS HKD ON VK.EH_KEY = HKD.EH_KEY
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
      where VK.EVT >= {dat1} and VK.EVT < {dat2} and VK.OGR_KEY = 7 and HKD.HKDFIL2_KEY = {HKDFIL}''' 
    DF = pd.read_sql(sql, conn)
    
    
    print(f'SQL finished {datetime.datetime.today()}')
    DF['EV'].fillna(0, inplace = True)
    DF['D'] = DF['VERKAUF'] + DF['EV']
    DF.D = DF.D.round(0)
    
    DF.loc[DF.BEZUG > DF.D, 'cost'] = (DF.BEZUG - DF.D) * c_o
    DF.loc[DF.BEZUG <= DF.D, 'cost'] = (DF.D - DF.BEZUG) * c_u  
    
    EH_cost = DF.groupby(['EH_KEY']).agg({'cost':'mean', 'VERKAUF': 'mean', 'D': 'mean', 'BEZUG':'count', 'EVT':'max'}).sort_values(by = ['cost'],ascending = False).reset_index()
    Worst50 = EH_cost[(EH_cost.BEZUG > 30) & (EH_cost.EVT > 20230101)].sort_values(by = ['cost'], ascending = False).head(50)  
    out = Worst50.EH_KEY.to_list()
    return out







def get_costs(start_date,shops):
    """
    shops must be a tuple
    """
    start_date_test = datetime.date(year = 2023, month = 2, day = 1)
    end_date_test = datetime.date.today()
    delta = end_date_test - start_date_test
    start_date2 = start_date + delta
    
    start_date = start_date.year*10000+start_date.month*100+start_date.day
    start_date_test = start_date_test.year*10000+start_date_test.month*100+start_date_test.day
    end_date_test = end_date_test.year*10000+end_date_test.month*100+end_date_test.day
    start_date2 = start_date2.year*10000+start_date2.month*100+start_date2.day
    
    conn  = sqlalchemy.create_engine('mssql://deaxsmapsql01.itservices.asudc.net,6200/Regulierungsstatistik?trusted_connection=yes&driver=SQL+Server', fast_executemany=True)
    sql = f'''select VK.EH_KEY, VK.EVT, VK.OBJ_KEY, VK.KALWT, (VK.BEZUG-VK.REMI) as VERKAUF, VK.BEZUG,  LS.EV as EV from 
    ablage.eh.tb_verkauf_mars AS VK LEFT JOIN [ANWENDUNG].[kpi].[TB_EH_S] AS HKD ON VK.EH_KEY = HKD.EH_KEY
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
      a.TIMESTAMP = b.MAXTIME and a.EH_KEY = b.EH_KEY and a.OBJ_KEY = b.OBJ_KEY and a.EVT = b.EVT) as LS ON VK.EH_KEY = LS.EH_KEY 
      and VK.OBJ_KEY = LS.OBJ_KEY and VK.EVT = (YEAR(LS.EVT)*10000 + MONTH(LS.EVT)*100 + DAY(LS.EVT)) 
      where VK.EVT >= {start_date} and VK.EVT <= {end_date_test} and VK.OGR_KEY = 7 and VK.EH_KEY in {shops}''' 
    DF_NEW_COSTS = pd.read_sql(sql, conn)  
    DF_NEW_COSTS['EV'].fillna(0, inplace = True)
    DF_NEW_COSTS['D'] = DF_NEW_COSTS['VERKAUF'] + DF_NEW_COSTS['EV']
    DF_NEW_COSTS.D = DF_NEW_COSTS.D.round(0)    
    DF_NEW_COSTS.loc[DF_NEW_COSTS.BEZUG > DF_NEW_COSTS.D, 'cost'] = (DF_NEW_COSTS.BEZUG - DF_NEW_COSTS.D) * c_o
    DF_NEW_COSTS.loc[DF_NEW_COSTS.BEZUG <= DF_NEW_COSTS.D, 'cost'] = (DF_NEW_COSTS.D - DF_NEW_COSTS.BEZUG) * c_u  
       
    OLD_COSTS = DF_NEW_COSTS[(DF_NEW_COSTS.EVT >= start_date) & (DF_NEW_COSTS.EVT < start_date_test)].copy()
    NEW_COSTS = DF_NEW_COSTS[(DF_NEW_COSTS.EVT >= start_date2) & (DF_NEW_COSTS.EVT < end_date_test)].copy()
    OLD_COSTS = OLD_COSTS.groupby(['EH_KEY', 'KALWT']).agg({'cost': ['sum','mean']}).reset_index()
    OLD_COSTS.columns = ['EH_KEY', 'KALWT', 'cost_old_sum', 'cost_old_avg']
    NEW_COSTS = NEW_COSTS.groupby(['EH_KEY', 'KALWT']).agg({'cost': ['sum','mean']}).reset_index().rename(columns = {'cost': 'cost_new'})
    NEW_COSTS.columns = ['EH_KEY', 'KALWT', 'cost_new_sum', 'cost_new_avg']
    OUT_DF = OLD_COSTS.merge(NEW_COSTS, on = ['EH_KEY', 'KALWT'], how = 'left')
    return OUT_DF
    
    
worst_shops_result = get_worst50shops(45501,20220101,20230301)
shops = tuple(worst_shops_result)
RESULT = newsvendor_complete(shops)
COSTS = get_costs(datetime.date(year = 2022, month = 1, day = 1),shops)
RESULT = RESULT.reset_index().merge(COSTS,on = ['EH_KEY','KALWT'], how = 'left')
