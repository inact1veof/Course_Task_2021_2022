import BatteryPackage

def Caclucate_Utility_For_Point(states,current_state, vec_u_opt):
    base_state = BatteryPackage.ComputeNextBaseState(current_state,states)
    base_costs = base_state[2] * base_state[7]
    new_opt_state = BatteryPackage.ComputeNextOptState(states, current_state, vec_u_opt)
    opt_costs = new_opt_state[2]*new_opt_state[7]
    return base_costs-opt_costs

def Caclucate_Utility_Per_Day(df):
    for i in range(1,df.shape[0]):
        if i % 23 != 0:
            df['utility'].iloc[i] = df['utility'].iloc[i-1] + df['utility'].iloc[i]
        else:
            df['utility'].iloc[i] = df['utility'].iloc[i]
    return df