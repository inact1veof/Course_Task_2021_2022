# influx db params
_host_influx = 'localhost'
_port_influx = 8086
_dbname_influx = 'ADP'
timeformat = '%d.%m.%Y %H:%M:%S'
importMetric = 'ImportData'
calcMetric = 'Calculated'

# sql db params
_connection_string = 'Server=localhost\SQLEXPRESS;Database=master;Trusted_Connection=True;'


#Q_learning params
N = 96
epsilon = 0.1
epoch = 25
reward = 0.1
