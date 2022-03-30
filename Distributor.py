import pandas as pd
import numpy as np
import InfluxModule
import SqlModule
import ModuleAPI
import Params
import Q_learning
import Metrics
from datetime import datetime as dt
import os


#start influxDB and Grafana from /soft
def init():
    print(f'[{dt.now().strftime("%H:%M:%S")}] Module starting, initialization')
    os.startfile(r'Soft\Influx\influxd.exe')
    print(f'[{dt.now().strftime("%H:%M:%S")}] InfluxDB started')
    os.startfile(r'Soft\Grafana\bin\grafana-server.exe')
    print(f'[{dt.now().strftime("%H:%M:%S")}] Grafana server started')

def getData(DATA_TYPE,FROM,CONTENT =[], TIMESTAMP = 0, CONDITION = ''):
    if DATA_TYPE == 'SQL':
        if FROM == "Attribute":
            if CONTENT != []:
                response = SqlModule.getAttributeId(CONTENT[0])
        if FROM == "Data":
            if CONTENT != []:
                response = SqlModule.getDataId(CONTENT[0], CONTENT[1])
        if FROM == "Utility":
            if CONTENT != []:
                response = SqlModule.getUtilityId(CONTENT[0], CONTENT[1])
    if DATA_TYPE == 'Inlfux':
        InfluxModule.Init()
        response, params, metric = InfluxModule.read_data_from_influx(TIMESTAMP,CONTENT,FROM, CONDITION)
        response = InfluxModule.transform_to_dataframe(response, params, metric)
    return response

def addData(DATA_TYPE,TO,CONTENT =[], TIMESTAMP = 0, LINK ='', CONDITION = ''):
    try:
        if CONDITION == '':
            if DATA_TYPE == 'Influx':
                InfluxModule.init()
                InfluxModule.crate_database()
                InfluxModule.write_data_to_influx(LINK)
            if DATA_TYPE == 'SQL':
                if TO == 'Attributes':
                    SqlModule.addAttribute(CONTENT[0])
                if TO == 'Data':
                    idAtr = SqlModule.getAttributeId(CONTENT[0])
                    SqlModule.addData(idAtr, CONTENT[1])
                if TO == 'Utility':
                    idAtr = SqlModule.getAttributeId(CONTENT[0])
                    idData = SqlModule.getDataId(idAtr, CONTENT[1])
                    SqlModule.addUtility(idData, CONTENT[2])
        if CONDITION == 'fit':
            print(f'[{dt.now().strftime("%H:%M:%S")}] Taking query for fit Q_learning')
            addData(DATA_TYPE, TO, CONTENT, LINK=LINK, CONDITION = '')
            df = InfluxModule.get_data_from_other(LINK)
            makeFit(df)
        if CONDITION == 'forecast':
            print(f'[{dt.now().strftime("%H:%M:%S")}] Taking query for forecast u_opt for dataframe')
            df = InfluxModule.get_data_from_other(LINK)
            makeForecast(df)
        return 1
    except Exception:
        return 0

def makeForecast(data):
    Q_learning.makePredict(data)

def makeFit(data):
    Q_learning.makeFit(data)

def updateData(DATA_TYPE,FROM, NEW_VALUE,CONTENT =[], TIMESTAMP = 0):
    try:
        if DATA_TYPE == 'SQL':
            if FROM == 'Attribute':
                idAtr = SqlModule.getAttributeId(CONTENT[0])
                SqlModule.update(idAtr, NEW_VALUE, FROM, CONTENT[0])
            if FROM == 'Data':
                idAtr = SqlModule.getAttributeId(CONTENT[0])
                idData = SqlModule.getDataId(idAtr,CONTENT[1])
                SqlModule.update(idData, NEW_VALUE, FROM, CONTENT[2])
            if FROM == 'Utility':
                idAtr = SqlModule.getAttributeId(CONTENT[0])
                idData = SqlModule.getDataId(idAtr, CONTENT[1])
                idUtility = SqlModule.getUtilityId(idData, CONTENT[2])
                SqlModule.update(idUtility, NEW_VALUE, FROM, CONTENT[3])
        if DATA_TYPE == 'Influx':
            df = pd.DataFrame(columns=['datetime', 'column', 'value'])
            df.append({'datetime': TIMESTAMP, 'column': FROM, 'value': NEW_VALUE })
            points = InfluxModule.transform_to_influx(df, Params.calcMetric)
            InfluxModule.write_points(points)
        return 1
    except Exception:
        return 0

def remove(DATA_TYPE,FROM, IDENTIFIER = 0,CONTENT =[]):
    try:
        if DATA_TYPE == 'SQL':
            if IDENTIFIER != 0:
                SqlModule.delete(IDENTIFIER, FROM, CONTENT)
            else:
                SqlModule.clearTable(FROM)
        if DATA_TYPE == 'Influx':
            InfluxModule.clear_data_influx()
        return 1
    except Exception:
        return 0

if __name__=='__main__':
    #addData('Influx','vec_u_opt', LINK ='https://raw.githubusercontent.com/inact1veof/Course_Task_2021_2022/main/data3_scenario_240day.csv', CONDITION = 'fit')
    #Q_Table = np.load('q_table.npy')
    #print(Q_Table)
    addData('Influx', 'vec_u_opt',
            LINK='https://raw.githubusercontent.com/inact1veof/Course_Task_2021_2022/main/test.csv',
            CONDITION='forecast')