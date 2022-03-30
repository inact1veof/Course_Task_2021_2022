# Module for work with timeseries
#use init, create_database
#after you can use each method

from datetime import datetime as dt
import time
from pytz import timezone
from influxdb import InfluxDBClient
import Params
import pandas as pd
import warnings
from math import ceil

warnings.simplefilter(action='ignore', category=FutureWarning)

client = InfluxDBClient(host=Params._host_influx, port=Params._port_influx)
metricImport = []
metricCalc = []

def init():
    client = InfluxDBClient(host=Params._host_influx, port=Params._port_influx)
    client.switch_database(Params._dbname_influx)
    metricImport = [Params.importMetric]
    metricCalc = [Params.calcMetric]

def crate_database():
    client = InfluxDBClient(host=Params._host_influx, port=Params._port_influx)
    client.create_database(Params._dbname_influx)
    client.drop_database(Params._dbname_influx)
    client.create_database(Params._dbname_influx)
    client.switch_database(Params._dbname_influx)

def get_data_from_other(link):
    data = pd.read_csv(link, sep=';', parse_dates=[['date', 'time']])
    data.drop(['DaloStatus', 'Model_used'], axis=1, inplace=True)
    data['date_time'] = data['date_time'].dt.strftime('%d.%m.%Y %H:%M:%S')
    data['date_time'] = pd.to_datetime(data['date_time'])
    print(f'[{dt.now().strftime("%H:%M:%S")}] Data was getting')
    return data

def parting(xs, parts):
    part_len = ceil(len(xs) / parts)
    return [xs[part_len * k:part_len * (k + 1)] for k in range(parts)]

def transform_to_influx(df, metric= [Params.importMetric]):
    points = []
    fields_coll = list(df.columns.values)[0:]
    epoch_naive = dt.utcfromtimestamp(60 * 60)
    epoch = timezone('UTC').localize(epoch_naive)
    for row in df.to_dict(orient='records'):
        datetime_naive = row['date_time']
        datetime_local = timezone('UTC').localize(datetime_naive)
        timestamp = int((datetime_local - epoch).total_seconds() * 1000) * 1000000
        tags = {}
        for tag in metric:
            t = metric[0]
            if tag in row:
                pass
            tags[tag] = t
        fields = {}
        for f in fields_coll[2:]:
            v = 0
            if f in row:
                v = float(row[f])
                fields[f] = v
        point = {"measurement": metric[0], "time": timestamp, "fields": fields, "tags": tags}
        points.append(point)
    print(f'[{dt.now().strftime("%H:%M:%S")}] {len(points)} data points is ready to write')
    return points

def write_data_to_influx(link):
    client = InfluxDBClient(host=Params._host_influx, port=Params._port_influx)
    client.switch_database(Params._dbname_influx)
    df = get_data_from_other(link)
    points = transform_to_influx(df)
    print(f'[{dt.now().strftime("%H:%M:%S")}] Making batches')
    points_to_write = parting(points, 10)
    print(f'[{dt.now().strftime("%H:%M:%S")}] Recording to InfluxDB')
    for i in range(len(points_to_write)):
        response = client.write_points(points_to_write[i])
        if (response == False):
            print(f'[{dt.now().strftime("%H:%M:%S")}] Write error')
        else:
            print(f'[{dt.now().strftime("%H:%M:%S")}] Batch {i + 1} of data successfully added to InfluxDB')
    print(f'[{dt.now().strftime("%H:%M:%S")}] All data was added')

def write_points(points):
    client = InfluxDBClient(host=Params._host_influx, port=Params._port_influx)
    client.switch_database(Params._dbname_influx)
    print(points[1])
    points_to_write = parting(points, 10)
    print(f'[{dt.now().strftime("%H:%M:%S")}] Recording to InfluxDB')
    for i in range(len(points_to_write)):
        response = client.write_points(points_to_write[i])
        if (response == False):
            print(f'[{dt.now().strftime("%H:%M:%S")}] Write error')
        else:
            print(f'[{dt.now().strftime("%H:%M:%S")}] Batch {i + 1} of data successfully added to InfluxDB')
    print(f'[{dt.now().strftime("%H:%M:%S")}] All data was added')

def read_data_from_influx(dates, params, metric, level):
    param_str = ",".join(params)
    if (level == ''):
        query = f"SELECT {param_str} FROM {metric} WHERE time > '{dates[0]}' AND time < '{dates[1]}'"
    if (level == 'Over'):
        query = f"SELECT {param_str} FROM {metric} WHERE time > '{dates[0]}'"
    if (level == 'Under'):
        query = f"SELECT {param_str} FROM {metric} WHERE time < '{dates[0]}'"
    if (level == 'One'):
        query = f"SELECT {param_str} FROM {metric} WHERE time = '{dates[0]}'"
    response = client.query(query)
    return response, params, metric

def transform_to_dataframe(response, params, metric):
    params.append('time')
    params.reverse()
    items = [point for point in response.get_points(measurement=metric)]
    result = pd.DataFrame(data=items, columns=params)
    return result

def clear_data_influx():
    client = InfluxDBClient(host=Params._host_influx, port=Params._port_influx)
    client.create_database(Params._dbname_influx)
    client.drop_database(Params._dbname_influx)
    client.create_database(Params._dbname_influx)
    client.switch_database(Params._dbname_influx)

