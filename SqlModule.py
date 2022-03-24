import pyodbc
import Params
from datetime import datetime as dt
import pandas as pd

global sqlClient
global cursor

def init():
    sqlClient = pyodbc.connect(Params._connection_string)
    cursor = sqlClient.cursor()

def addAttribute(param_name):
    query = f'INSERT Attribute VALUES({param_name})'
    cursor.execute(query)
    print(f'[{dt.now().strftime("%H:%M:%S")}] Attribute: {param_name} added')

def addData(attribute_id, value):
    query = f'INSERT Data VALUES({attribute_id}, {value})'
    cursor.execute(query)
    print(f'[{dt.now().strftime("%H:%M:%S")}] Data: {value} added to attribute id = {attribute_id}')

def addUtility(data_id, value):
    query = f'INSERT Utility VALUES({data_id}, {value})'
    cursor.execute(query)
    print(f'[{dt.now().strftime("%H:%M:%S")}] Utility: {value} added to data id = {data_id}')

def getAttributeId(name):
    query = f'SELECT id FROM Attribute WHERE Attribute.Name = {name}'
    cursor.execute(query)
    return int(cursor[0])

def getDataId(attribute_id, value):
    query = f'SELECT id FROM Data WHERE Attribute_Id = {attribute_id} AND Value = {value}'
    cursor.execute(query)
    return int(cursor[0])

def getUtilityId(data_id, value):
    query = f'SELECT id FROM Utility WHERE Data_Id = {data_id} AND Value = {value}'
    cursor.execute(query)
    return int(cursor[0])

def delete(id, table):
    query = f'DELETE FROM {table} WHERE {table}.Id = {id}'
    cursor.execute(query)
    print(f'[{dt.now().strftime("%H:%M:%S")}] Value from {table} id = {id} deleted')

def update(id, new_value, table, field):
    query = f'UPDATE {table} SET {table}.{field} = {new_value} WHERE {table}.Id = {id}'
    cursor.execute(query)
    print(f'[{dt.now().strftime("%H:%M:%S")}] Attribute id = {id} updated')

def clearTable(table):
    query = f'DELETE FROM {table}'
    cursor.execute(query)
    print(f'[{dt.now().strftime("%H:%M:%S")}] Table: {table} cleared')

def transform_to_dataframe(table, params, condition):
    param_str = ",".join(params)
    query = f'SELECT {param_str} FROM {table} {condition}'
    cursor.execute(query)
    items = [row for row in cursor]
    result = pd.DataFrame(data=items, columns=params)
    return result
