import pandas as pd
import numpy as np
import Distributor
import InfluxModule
import Params
from datetime import datetime as dt
import random
import Metrics

class QLearning:

    def __init__(self, eps, epoch, states, actions, reward, q_table = [], state = [], data = [], N = 0):
        self.eps = eps
        self.epoch = epoch
        self.state = state
        self.states = states
        self.actions = actions
        self.reward = reward
        self.q_table = q_table
        self.vec_u_opt = []
        self.utility_history = []
        self.data = data
        self.counter = 0
        self.N = Params.N

    def fit(self):
        self.state = self.states[0]
        for e in range(self.epoch):
            print(f'[{dt.now().strftime("%H:%M:%S")}] Epoch: {e+1}')
            for i in range(self.N):
                if self.counter >= len(self.states)-2:
                    self.counter = 0
                self.makeAction()
                self.state = self.getState()

    def predict(self, dataframe):
        states_for_predict = MakeStateVec(dataframe)
        self.counter = 31
        for i in range(len(states_for_predict)):
            self.state = states_for_predict[i]
            tmp = np.array(self.state)
            tmp_st = np.array(self.states)
            q_table_line = self.counter
            max = np.max(self.q_table[q_table_line])
            index, = np.where(self.q_table[q_table_line] == max)
            u_opt = self.actions[index[0]]
            utility = self.calc_utility(u_opt)
            self.vec_u_opt.append(u_opt)
            self.utility_history.append(utility)
            self.counter += 1
        return self.vec_u_opt

    def calc_utility(self, u_opt):
        return Metrics.Caclucate_Utility_For_Point(self.states,self.state, u_opt, self.counter)

    def getState(self):
        res = self.states[self.counter]
        self.counter += 1
        return res

    def makeAction(self):
        tmp = np.array(self.state)
        tmp_st = np.array(self.states)
        q_table_line = find_index(tmp_st, tmp)[0]
        max = np.max(self.q_table[q_table_line])
        if max == 0 or max < 0:
            index = random.randint(0, len(self.actions)-1)
            u_opt = self.actions[index]
            utility = self.calc_utility(u_opt)
            if utility > 0:
                self.q_table[q_table_line, index] += self.reward
            else:
                self.q_table[q_table_line, index] -= self.reward
        else:
            index, = np.where(self.q_table[q_table_line] == max)
            u_opt = self.actions[index[0]]
            utility = self.calc_utility()
            if utility > 0:
                self.q_table[q_table_line, index] += self.reward
            else:
                self.q_table[q_table_line, index] -= self.reward
        self.vec_u_opt.append(u_opt)
        self.utility_history.append(utility)


def Init(df, param):
    if (param == 'fit'):
        print(f'[{dt.now().strftime("%H:%M:%S")}] Initialization of Q_Learning for fit')
        df = df[["SoC_End_Pct", "E_load_Wh", "E_from_grid_Wh", "E_to_grid_Wh", "E_from_bat_Wh",
                 "E_to_bat_Wh_solar", "Tariff_income_Eur", "Tariff_expense_Eur"]]
        States = MakeStateVec(df)
        Actions = MakeActionVec()
        Q_table = MakeQTable(len(States), len(Actions))
        model = QLearning(eps=Params.epsilon, epoch=Params.epoch, states=States, actions=Actions, reward=Params.reward, q_table=Q_table, data=df)
        print(f'[{dt.now().strftime("%H:%M:%S")}] Starting fit')
        model.fit()
        print(f'[{dt.now().strftime("%H:%M:%S")}] Fit is end')
        print(f'[{dt.now().strftime("%H:%M:%S")}] Saving fit data')
        SaveQ_table(model)
    if (param == 'predict'):
        print(f'[{dt.now().strftime("%H:%M:%S")}] Initialization of Q_Learning with current Q-table')
        States = np.load('states.npy')
        Actions = np.load('actions.npy')
        Q_Table_load = np.load('q_table.npy')
        print(f'[{dt.now().strftime("%H:%M:%S")}] Q_table is successfully loaded')
        df_original = df.copy(deep=True)
        df = df[["SoC_End_Pct", "E_load_Wh", "E_from_grid_Wh", "E_to_grid_Wh", "E_from_bat_Wh",
                 "E_to_bat_Wh_solar", "Tariff_income_Eur", "Tariff_expense_Eur"]]
        model = QLearning(eps=Params.epsilon, epoch=Params.epoch, states=States, actions=Actions, reward=Params.reward,
                          q_table=Q_Table_load, data=df)
        start = df_original['date_time'][0]
        stop = df_original['date_time'][df.shape[0]-1]
        print(f'[{dt.now().strftime("%H:%M:%S")}] Making forecast for dates: {start} to {stop}')
        print(f'[{dt.now().strftime("%H:%M:%S")}] Calculating u_opt with {df.shape[0]} points')
        result = model.predict(df)
        Utility_History = model.utility_history
        print(f'[{dt.now().strftime("%H:%M:%S")}] Final! Writing to Inlfux Database')
        data_for_export = Transform_Data(df_original, result, Utility_History)
        Write_to_db(data_for_export)
        print(f'[{dt.now().strftime("%H:%M:%S")}] Done')


def Write_to_db(data):
    points = InfluxModule.transform_to_influx(data, [Params.calcMetric])
    InfluxModule.write_points(points)

def asvoid(arr):
    arr = np.ascontiguousarray(arr)
    return arr.view(np.dtype((np.void, arr.dtype.itemsize * arr.shape[-1])))

def find_index(arr, x):
    arr_as1d = asvoid(arr)
    x = asvoid(x)
    return np.nonzero(arr_as1d == x)[0]

def SaveQ_table(model):
    states = np.array(model.states)
    actions = np.array(model.actions)
    q_table = np.array(model.q_table)
    np.save('states', states)
    np.save('actions', actions)
    np.save('q_table', q_table)

def Transform_Data(df_with_dt, vec_u_opt, utility_history):
    temp = pd.DataFrame(columns=['date_time','0' 'u_opt', 'utility'])
    for i in range(len(vec_u_opt)):
        point = {'date_time': df_with_dt['date_time'].iloc[i],'utility_total': 0, 'u_opt': vec_u_opt[i], 'utility': utility_history[i]}
        temp = temp.append(point, ignore_index=True)
    result = Metrics.Caclucate_Utility_Per_Day(temp)
    return result


def MakeQTable(lines, columns):
    print(f'[{dt.now().strftime("%H:%M:%S")}] Making Q_table')
    q_table = np.zeros(shape=[lines, columns])
    return q_table

def MakeState(series):
    State = np.zeros(len(series))
    for i in range(len(series)):
        State[i] = series[i]
    return State

def MakeActionVec():
    print(f'[{dt.now().strftime("%H:%M:%S")}] Making actions vec')
    result = []
    start = 0
    eps = Params.epsilon
    while (start < 1):
        result.append(start)
        start+=eps
    return result

def MakeStateVec(data):
    #data = data.drop_duplicates()
    print(f'[{dt.now().strftime("%H:%M:%S")}] Making states vec')
    States = []
    for i in range(data.shape[0]):
        tmp_state = MakeState(data.iloc[i])
        States.append(tmp_state)
    return States

def makeFit(df):
    Init(df, 'fit')

def makePredict(df):
    Init(df, 'predict')
