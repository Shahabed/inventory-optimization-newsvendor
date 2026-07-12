# -*- coding: utf-8 -*-
"""
Created on Thu Jun 22 07:06:49 2023

@author: S.C.Azizbadi
"""

import datetime
import pandas as pd
import sqlalchemy
import numpy as np

c_u = 0.8679 - 0.105
c_o = 0.105 - 0.001254

shopsdf = pd.read_excel("20230515_MO_First_Test_45501.xlsx")
shops = tuple(shopsdf.EH_KEY.drop_duplicates())

def newsvendor_complete(shops):
    """Return the optimal quantities for every shop and every weekday for OGR = 7"""
    #load data
    print(f'start {datetime.datetime.today()}')
    conn  = sqlalchemy.create_engine('mssql://deaxsmapsql01.itservices.asudc.net,6200/Regulierungsstatistik?trusted_connection=yes&driver=SQL+Server', fast_executemany=True)
    sql = f'''select VK.EH_KEY, VK.OBJ_KEY, VK.EVT, VK.KALWT, (VK.BEZUG-VK.REMI) as VERKAUF, VK.BEZUG,  LS.EV as EV from ablage.eh.tb_verkauf_mars AS VK 
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
    where VK.EVT >= 20230501 and VK.OGR_KEY = 7 and VK.EH_KEY in {shops}''' 
    DF = pd.read_sql(sql, conn)
    print(f'SQL finished {datetime.datetime.today()}')
    #replace NaNs with 0, so calc_newsvendor won't produce NaNs
    DF['EV'].fillna(0, inplace = True)
    #create Demand
    DF['D'] = DF['VERKAUF'] + DF['EV']
    DF.D = DF.D.round(0)
    #apply calc_newsvendor function on every groupby element
    # DF_NV = DF.groupby([ 'OBJ_KEY', 'EH_KEY', 'KALWT'], group_keys=False).D.apply(calc_newsvendor)
    # print(f'Calculation finished {datetime.datetime.today()}')
    # DF = DF.merge(DF_NV.reset_index().rename(columns = {'D':'OPT'}), on = [ 'OBJ_KEY', 'EH_KEY', 'KALWT'], how = 'left')
    # DF.groupby([ 'OBJ_KEY', 'EH_KEY', 'KALWT'], group_keys=False).apply(Plot_NV)
    return DF

DF = newsvendor_complete(shops)

DF['AV'] = np.where(DF.VERKAUF == DF.BEZUG,1, 0)




# EVT start Test: 
start_test = 20230515
    
#max EVt with lostsales:  20230527
maxEVT = DF[DF.EV > 0].EVT.max()


#sold out quota before test:
AVQ_before =(  (DF[DF.EVT < start_test]['AV'].sum() / DF[DF.EVT < start_test].shape[0] ))* 100

#not sol out before test
noAVQ_befrore = 100 - AVQ_before

#sold out quota with test
AVQ_ist =(  (DF[(DF.EVT >= start_test) & (DF.EVT <= maxEVT)]['AV'].sum() / DF[(DF.EVT >= start_test) & (DF.EVT <= maxEVT)].shape[0] ))* 100

#not sol out with test
noAVQ_IST = 100 - AVQ_ist




#add costs (overage underage)
DF.loc[DF.BEZUG > DF.D, 'cost'] = (DF.BEZUG - DF.D) * c_o
DF.loc[DF.BEZUG <= DF.D, 'cost'] = (DF.D - DF.BEZUG) * c_u


#mean costs before test per shop and evt
Cost_beforeTest = DF.loc[DF.EVT < start_test, 'cost'].mean()
    
#men costs with test per shop and evt
Cost_whileTest = DF.loc[(DF.EVT >= start_test) & (DF.EVT <= maxEVT), 'cost'].mean()

# cost reduction in percent
cost_red_perc = (Cost_whileTest - Cost_beforeTest) / Cost_beforeTest * 100

DF['date'] = pd.to_datetime(DF.EVT, format = '%Y%m%d') 


#20230518 was holiday!!!! Attention

#show Demand Bezug and Sales
def show_timeline(DF,shop):
    DF = DF[DF.EH_KEY == shop].sort_values(by = ['EVT']).reset_index().copy()
    import matplotlib.pyplot as plt
    plt.plot(DF['date'],DF.BEZUG)
    plt.plot(DF['date'],DF.D)
    plt.vlines(DF[DF.EVT == start_test]['date'], ymin = DF.D.min(), ymax = DF.BEZUG.max(), colors= 'green')
    plt.legend(['BEZUG', 'Nachfrage'])
    plt.show()


for shop in DF.EH_KEY.drop_duplicates():
    DF_temp = DF[(DF.EVT <= maxEVT) & (DF.EH_KEY == shop)].sort_values(['EVT'])
    #print(DF_temp[['EH_KEY','EVT','KALWT','BEZUG','D']])
    show_timeline(DF_temp,shop)
    
    






