# -*- coding: utf-8 -*-
"""
Created on Tue Dec 21 20:15:03 2021

@author: AVKychkin507
"""
import Calc
import P

def ComputeAvailableBatteryEnergy_b(SOC,c_max,d_max,s_max):                    # Compute Optimal Activation DA
	available_energy = 0
	SOC_tmp = SOC
	available_energy = 0
	for t in range(0,P.FutureSteps): 
		if (SOC_tmp > 0):
			res = min((d_max*P.DT*P.eta_d), (SOC*s_max*P.eta_d))
			available_energy += res
			SOC_tmp -= res / P.eta_d / s_max
		if (SOC_tmp < 0):
			SOC_tmp = 0
	return available_energy

def ComputeRequiredBatteryEnergy_b(SOC,c_max,d_max,s_max):
	required_energy = 0
	SOC_tmp = SOC
	required_energy = 0
	for t in range (0,P.FutureSteps):
		if (SOC_tmp < 1):
			res = min((c_max*P.DT*P.eta_c), ((1-SOC)*s_max*P.eta_c))
			required_energy+= res
			SOC_tmp+= res / P.eta_c / s_max
		if (SOC_tmp > 1):
			SOC_tmp = 1
	return required_energy

def ComputeFutureEnergyExchange(SOC,Vc_act,Vd_act,DP_future_b,c_max,d_max,s_max):  
    AvailableBatteryEnergy = ComputeAvailableBatteryEnergy_b(SOC,c_max,d_max,s_max)
    RequiredBatteryEnergy = ComputeRequiredBatteryEnergy_b(SOC,c_max,d_max,s_max)

    Vc_need = 0
    Vd_feed = 0
    NeedAfter_b = 0
    FeedAfter_b = 0

    NeedAfter_b = (DP_future_b * P.DT) + AvailableBatteryEnergy
    if (NeedAfter_b > 0):
        NeedAfter_b = 0
        
    FeedAfter_b = (DP_future_b * P.DT) - RequiredBatteryEnergy
    if (FeedAfter_b < 0):
        FeedAfter_b = 0
    
    if (DP_future_b*P.DT > 0):
        if (DP_future_b * P.DT > RequiredBatteryEnergy):                         # DP > 0, which implies that there is more PV than Load, and as a result the battery will be charged
            ChargeAfter_b = RequiredBatteryEnergy
            DischargeAfter_b = 0		
        else:
            ChargeAfter_b = DP_future_b * P.DT
            DischargeAfter_b = 0			
    else: 
        if (-DP_future_b*P.DT > AvailableBatteryEnergy):                         # in this case, the Load is higher than the PV, and the battery will be discharge (at least on average)
            DischargeAfter_b = AvailableBatteryEnergy
            ChargeAfter_b = 0
        else:
            DischargeAfter_b = DP_future_b*P.DT
            ChargeAfter_b = 0
    
    if (NeedAfter_b < 0):
        Vc_need = min(-NeedAfter_b, Vc_act)
    if (FeedAfter_b > 0):	
        Vd_feed = max(-FeedAfter_b, Vd_act)	
        
    return NeedAfter_b,FeedAfter_b,ChargeAfter_b,DischargeAfter_b,Vc_need,Vd_feed
	 
def ComputeBaseline(_dP,SOC,c_max,d_max,s_max):                                
    DTc_max_tmp = (1 - SOC)*s_max / c_max / P.eta_c                              # DTc_max_tmp - the minimum time takes for the battery to be full
    Pb_c_max = c_max*min(DTc_max_tmp, P.DT)/P.DT                                   # the maximum charging rate to the battery in this interval
    DTd_max_tmp=SOC*s_max*P.eta_d/d_max                                          # DTd_max_tmp
    Pb_d_max = -d_max*min(DTd_max_tmp, P.DT)/P.DT        
        
    if (_dP >= 0):                                                             # average PV - Load
        Pb_base = min(Pb_c_max,_dP)
    else:
        Pb_base = max(Pb_d_max,_dP)  
            
    Vc = (Pb_c_max - Pb_base)*P.DT                                               # Computing the available Charging Potential over the next interval
    if (Vc < 0):
        Vc = 0        
    Vc_act = Vc 
                            
    Vd = (Pb_d_max - Pb_base)*P.DT                                               # Computing the available Discharing Potential over the next interval                            
    if (Vd > 0):
        Vd = 0       
    Vd_act = Vd 
               
    Pg_base = Pb_base - _dP        
    return Pg_base, Pb_base, Vd, Vc, Vd_act, Vc_act, Pb_d_max, Pb_c_max

def ComputeNextState(Pb,DP_next,SOC,c_max,d_max,s_max):                        # State of charge of battery at time i+1 
    SOC_tmp = SOC                                                              # We first calculate the change in the SOC due to the baseline power to the battery (this is the baseline power to the battery for this interval, based on DP = PV - Load, if DP > 0, Pb = DP )
    if (Pb >= 0):                                                              # this implies that the baseline power to the battery is positive (the battery is charging)
        SOC_tmp+= Pb*P.DT*P.eta_c/s_max		
    else:
        SOC_tmp+= Pb*P.DT/P.eta_d/s_max

    if (SOC_tmp < 0):                                                          # Constraints on the SOC of the battery
        SOC_tmp = 0
    if (SOC_tmp > 1):
        SOC_tmp = 1

    DTc_max_tmp = (1 - SOC_tmp)*s_max / c_max / P.eta_c                          # Computing the baseline power to the battery
    Pb_c_max = c_max*min(DTc_max_tmp, P.DT) / P.DT    
    DTd_max_tmp = SOC_tmp*s_max/d_max
    Pb_d_max = -d_max*min(DTd_max_tmp, P.DT)*P.eta_d / P.DT    

    if (DP_next >= 0):                                                         # there is an excess power that will charge the battery (for as long as this is possible), the rest will be fed into the grid
        Pb_baseline_next = min(Pb_c_max, DP_next)		
    else:
        Pb_baseline_next = max(Pb_d_max, DP_next)
		
    Vc_next = (Pb_c_max - Pb_baseline_next)*P.DT
    if (Vc_next < 0):
        Vc_next = 0
        
    Vd_next = (Pb_d_max - Pb_baseline_next)*P.DT
    if (Vd_next > 0):
        Vd_next = 0	
        
    Pg_next = Pb_baseline_next - DP_next        
    return Vc_next, Vd_next, SOC_tmp, Pb_baseline_next, Pg_next, Pb_c_max, Pb_d_max


""" This function provides the optimal activation details, given the decision with respect to the optimal DA action """
def ComputeOptimalActivation_DA(e_schedule,SOC_current,DP_forecast_day,DP_forecast_next_day,current_interval_ind,autonomous_operation,c_max,d_max,s_max):
    total_base_schedule = 0
    Pb_actual = 0
    Pb_base_actual = 0
    Vc_tmp = 0
    Vd_tmp = 0
    Vc_act_tmp = 0
    Vd_act_tmp = 0  	
                                        									   # Note that the u_opt, has been computed based on the active potential, and therefore when we compute the commitment, we need to use the same potential.
    total_commitment = 0                                                       # summarize the total energy commitment in the DA market on this 15min interval
    Eb_commitment = 0					                                       # total commitment from each household
    Eb_c_commitment = 0					                                       # charging commitment from each household
    Eb_d_commitment = 0					                                       # discharging commitment from each household
    Eb_commitment_battery = 0				                                   # total commitment from the battery
    Eb_c_commitment_battery = 0				                                   # total charging commitment from the battery
    Eb_d_commitment_battery = 0				                                   # total discharging commitment from the battery
    u_remain = 0                                                               # u_remain summarizes the total potential that should be extracted		      
                     
    DP_forecast_future_b = Calc.DP_forecast_future_b_calc(DP_forecast_day,DP_forecast_next_day)
    Pg_base, Pb_base, Vd, Vc, Vd_act, Vc_act, Pb_d_max, Pb_c_max = ComputeBaseline(DP_forecast_day[current_interval_ind],SOC_current,c_max,d_max,s_max)
    
    total_base_schedule += Pg_base*P.DT
	
    NeedAfter_b,FeedAfter_b,ChargeAfter_b,DischargeAfter_b,Vc_need,Vd_feed = ComputeFutureEnergyExchange(SOC_current,Vc_act,Vd_act,DP_forecast_future_b[current_interval_ind],c_max,d_max,s_max)
										                                  
    Pb_actual = Pb_base	                                                       # we initialize the actual Pb from the current baseline. any activations are computed on top of this baseline 
    Pb_base_actual = Pb_base  
    Vc_tmp = Vc
    Vd_tmp = Vd
    Vc_act_tmp = Vc_act
    Vd_act_tmp = Vd_act			
    
    if (autonomous_operation==False): 
        total_commitment = e_schedule - total_base_schedule	                   # keeping track of the total commitment	
    else:
        total_commitment = 0
    
    if (total_commitment > 0): 
        if (total_commitment >= Vc): 						                   # in case the total commitment is >0, which implies that charging flexibility is requested
            u_remain = Vc		
        else: 
            u_remain = total_commitment		
                              
# To determing the part of the energy that can be provided for free, we utilize the Pb_base, which determines the power to the battery under the preferences of the user
# in case, this battery is going to need energy and the baseline battery operation is currently discharging then by stopping the discharge of the battery, we create charging potential       
# we have used the additional constraint that the active potential of this battery is >0 (even if this is a free potential, it might be better to constrain the activations withinthe batteries that are considered 'active')
# if we are here, then this means that this is an active battery, so we are willing to provide all of its free potential                                          
        
        if ((NeedAfter_b < 0) and (Pb_base_actual < 0) and (Vc_act_tmp > 0)):         
            tmp = min(-Pb_base_actual * P.DT, -NeedAfter_b)
            if (u_remain >= tmp): 			                                   # if the requested flexibility is larger than the available quantity in this battery that we can use														
                u_remain -= tmp
                Eb_commitment = tmp				                               # the household then is used to activate 'tmp' energy
                Eb_c_commitment = tmp				                           # this also corresponds to charging flexibility
                Vc_tmp -= tmp
                Vc_act_tmp -= tmp
                if (tmp >= -NeedAfter_b): 					
                    NeedAfter_b = 0					
                else:
                    NeedAfter_b += tmp					
                Pb_actual += tmp / P.DT			                               # the actual power to the battery is increasing
                Eb_commitment_battery = 0				                       # the battery is not directly used yet
            else:
                Eb_commitment = u_remain
                Eb_c_commitment = u_remain
                Eb_commitment_battery = 0
                Vc_tmp -= u_remain
                Vc_act_tmp -= u_remain
                Pb_actual += u_remain / P.DT
                if (u_remain >= -NeedAfter_b): 
                    NeedAfter_b += u_remain					
                else: 
                    NeedAfter_b = 0					
                u_remain = 0								
											                                   # At this point, any available free charging potential has been already assigned 
											                                   # to the households. We need to assign the remaining of the commitment, which is going to be charged directly to the battery.
        if (u_remain > 0):					                                   # in this case, there is still potential that need to be covered, i.e., any free potentialhas already been used, from 'all' the available batteries.
											                                   # below we start using only the 'cheap' batteries the new baseline power becomes the current one
            Pb_base_actual = Pb_actual						                    
            if ((NeedAfter_b < 0) and (Vc_act_tmp > 0)):		               # again in order to assign any charging potential, we are going to use batteries that
											                                   # a. need energy within the upcoming hours
											                                   # b. belong to the class of active batteries
                tmp = min(-NeedAfter_b, Vc_act_tmp)                            # we define the quantity 'tmp' which aggregates the maximum quantity that this battery could provide without causing any issues in the baseline cost
                if (u_remain >= tmp): 					
                    u_remain -= tmp
                    Eb_commitment += tmp			                           # this quantity goes directly to the battery
                    Eb_c_commitment += tmp			                           # and corresponds to charging potential
                    Pb_actual += tmp / P.DT			                           # this is the new power to the battery after the new commitment
                    Vc_tmp -= tmp
                    Vc_act_tmp -= tmp
                    NeedAfter_b += tmp
                    if (Pb_base_actual >= 0):  		                           # if the battery is currently charging, any additional commitment goes directly to the battery
                        Eb_commitment_battery += tmp
                        Eb_c_commitment_battery += tmp
                    elif ((Pb_base_actual<0) and (tmp > -Pb_base_actual*P.DT)): 
                        Eb_commitment_battery+= tmp + Pb_base_actual*P.DT
                        Eb_c_commitment_battery+= tmp + Pb_base_actual*P.DT												
                else:                                                           # this implies that the remaining commitment is smaller than the available flexibility                               										   
                    Eb_commitment += u_remain
                    Eb_c_commitment += u_remain
                    Pb_actual += u_remain / P.DT
                    Vc_act_tmp += -u_remain
                    Vc_tmp += -u_remain
                    NeedAfter_b += u_remain
                    if (Pb_base_actual >= 0): 					               # this implies that the battery is currently charging, so any additional commitment goes directly to the battery
                        Eb_commitment_battery += u_remain
                        Eb_c_commitment_battery += u_remain						
                    elif ((Pb_base_actual<0) and (u_remain > -Pb_base_actual*P.DT)): 
                        Eb_commitment_battery+= u_remain + Pb_base_actual*P.DT
                        Eb_c_commitment_battery += u_remain + Pb_base_actual * P.DT						
                    u_remain = 0								
                                                        					   # We now go through all the batteries than need energy in the near future, and which are not among the active batteries
        if (u_remain > 0):		                                               # In this case, we have additional commitment that we need to cover, and we have to use the batteries that are not 'active'.									                                           
									                                           # Again, however, it would be better to use first the batteries that have NeedAfter(b) < 0
            Pb_base_actual = Pb_actual                                         # given that NeedAfter_b < 0, first, we will have the batteries that need the most energy									                                           
			                                                                   # we first use the batteries that have NeedAfter<0, and positive charging potential
            if ((NeedAfter_b < 0) and (Vc_tmp > 0)):				
                tmp = min(-NeedAfter_b, Vc_tmp)                                # > 0
                if (u_remain >= tmp):					                       # if the required charging commitment is larger than the available charging 	
                    u_remain -= tmp                                            # potential of this battery, then we need to use all the available potential
                    Eb_commitment += tmp
                    Eb_c_commitment += tmp
                    Pb_actual += tmp / P.DT
                    Vc_tmp -= tmp
                    NeedAfter_b += tmp												
                    if (Pb_base_actual >= 0):                                  # we finally need to determine which part of this commitment goes to the battery						
                        Eb_commitment_battery += tmp                           # if the battery is currently charging, all the commitment will go the battery
                        Eb_c_commitment_battery += tmp						
                    elif ((Pb_base_actual < 0) and (tmp > -Pb_base_actual*P.DT)):# if the battery is currently discharging, some of this potential can be used for free depending on the current baseline power
                        Eb_commitment_battery += tmp + Pb_base_actual * P.DT
                        Eb_c_commitment_battery += tmp + Pb_base_actual * P.DT		
                else:					
                    Eb_commitment += u_remain 					               # this potential goes directly to the battery
                    Pb_actual += u_remain / P.DT
                    Vc_tmp += -u_remain
                    NeedAfter_b = NeedAfter_b + u_remain
                    if (Pb_base_actual >= 0): 						
                        Eb_commitment_battery += u_remain
                        Eb_c_commitment_battery += u_remain						
                    elif ((Pb_base_actual<0) and (u_remain>-Pb_base_actual*P.DT)):															
                        Eb_commitment_battery += u_remain + Pb_base_actual*P.DT  # this means that the remaining commitment will be partially be covered by free potential (equal to Pb_base_actual*DT, and the remaining one goes to the battery
                        Eb_c_commitment_battery += u_remain + Pb_base_actual*P.DT						
                    u_remain = 0
                             			                                       # in case there is still potential that need to be covered, then we use the remaining of the batteries with positive potential overall
        if (u_remain > 0): 		
            Pb_base_actual = Pb_actual
            if (u_remain >= Vc_tmp): 										   # if the required charging commitment is larger than the available charging potential of this battery, then we need to use all the available potential
                u_remain -= Vc_tmp
                Eb_commitment += Vc_tmp
                Eb_c_commitment+= Vc_tmp
                Pb_actual+= Vc_tmp/P.DT
                if (Pb_base_actual>= 0):                                       # if the battery is currently charging, all the commitment will go the battery
                    Eb_commitment_battery+= Vc_tmp
                    Eb_c_commitment_battery+= Vc_tmp					
                elif ((Pb_base_actual<0) and (Vc_tmp>-Pb_base_actual*P.DT)): 	   # if the battery is currently discharging, some of this potential can be used for free depending on the current baseline power
                    Eb_commitment_battery += Vc_tmp + Pb_base_actual*P.DT
                    Eb_c_commitment_battery += Vc_tmp + Pb_base_actual*P.DT					
                Vc_tmp=0				
            else:
                Eb_commitment+= u_remain                        			   # this potential goes directly to the battery
                Pb_actual+= u_remain / P.DT
                Vc_tmp+= -u_remain
                if (Pb_base_actual >= 0):
                    Eb_commitment_battery += u_remain
                    Eb_c_commitment_battery += u_remain					
                elif ((Pb_base_actual<0) and (u_remain > -Pb_base_actual*P.DT)): # this means that the remaining commitment will be partially be covered by free potential (equal to Pb_base_actual*DT, and the remaining one goes to the battery
                    Eb_commitment_battery+= u_remain + Pb_base_actual*P.DT
                    Eb_c_commitment_battery+= u_remain + Pb_base_actual*P.DT					
                u_remain = 0				
	
    elif (total_commitment < 0):										
        if (total_commitment <= Vd):                                           # in this case, we have a discharging overall commitment
            u_remain = Vd		
        else:
            u_remain = total_commitment     								   # we first check which batteries can provide free flexibility, and we first assign to them as more flexibility as possible

        if ((FeedAfter_b>0) and (Pb_base_actual>0) and (Vd_act_tmp<0)):        # if the battery is going to feed-in energy in the near future, and it is currently charging, and it is one of the active batteries,
										                                       # then by reducing the discharging of the battery we are able to generate discharging potential. we do not want to utilize larger
										                                       # potential than these two quantities in order not to create additional costs
            tmp = min(FeedAfter_b, Pb_base_actual * P.DT)
            if (u_remain <= -tmp): 
                u_remain += tmp
                Eb_commitment -= tmp
                Eb_d_commitment -= tmp
                Vd_tmp += tmp				                                   # the discharging potential reduces
                Vd_act_tmp += tmp				                               # the active discharging potentail reduces
                Pb_actual += -tmp / P.DT	 		                               # the power to the battery reduces, since we reduce the charging
                if (tmp < FeedAfter_b): 
                    FeedAfter_b += -tmp					
                else:
                    FeedAfter_b = 0										
                    Eb_commitment_battery = 0                                  # in this case, the commitment that comes directly from the batteries is zero.
                    Eb_d_commitment_battery = 0				
            else: 				                                               # in this case, all the remaining commitment can be covered from the available free potential of the batteries				
                Eb_commitment += u_remain			                           # note that this has a negative sign (discharging)
                Eb_d_commitment += u_remain			                           # note that this has a negative sign (discharging)
                Vd_tmp += -u_remain				                               # the discharging potential reduces
                Vd_act_tmp += -u_remain			                               # the discharging potential reduces
                Pb_actual += u_remain / P.DT
                FeedAfter_b += u_remain
                u_remain = 0					
                Eb_commitment_battery = 0                                      # in this case, the battery is not used for generating this flexibility
                Eb_d_commitment_battery = 0				

# some of the batteries have already been selected to provide free flexibility, which implies that the baseline power to the battery has now changed
        if (u_remain < 0): 		
            Pb_base_actual = Pb_actual  						               # we update the baseline power to the battery
            if ((FeedAfter_b>0) and (Vd_act_tmp<0)):                           # we consider the batteries that are going to feed-in energy in the near future
																			   # using this available discharging potential will not create costs due to differences with the baseline operation of the battery
                tmp = min(-Vd_act_tmp, FeedAfter_b) 			               # > 0
                            												   # we would like not to use more flexibility than the FeedAfter, in order not to create any additional costs due to the baseline differences
                if (u_remain <= -tmp): 
                    u_remain += tmp						                       # the remaining commitment is reduced
                    Eb_commitment+= -tmp  					                   # we have a negative commitment from the household
                    Eb_d_commitment+= -tmp
                    Pb_actual+= -tmp / P.DT  					                   # the battery is discharging
                    Vd_tmp+= tmp						                       # then the discharging potential is reduced
                    Vd_act_tmp+= tmp
                    FeedAfter_b+= -tmp
						
                    if (Pb_base_actual<= 0):                                   # if the battery is currently discharging, any additional commitment will come directly from the battery													
                        Eb_commitment_battery+= -tmp			               # this flexibility comes from the battery
                        Eb_d_commitment_battery+= -tmp
					
                    elif ((Pb_base_actual>0) and (tmp>=Pb_base_actual*P.DT)): 
							                                                   # if the battery is currently charging, then part of it will come from the battery and part of it by blocking the current charging
                        Eb_commitment_battery+=tmp-Pb_base_actual*P.DT
                        Eb_d_commitment_battery+=tmp-Pb_base_actual*P.DT							
                else: 
                    Eb_commitment+=u_remain
                    Eb_d_commitment+= u_remain
                    Pb_actual+= u_remain / P.DT
                    Vd_tmp+= -u_remain
                    Vd_act_tmp+= -u_remain
                    FeedAfter_b+= u_remain
                    if (Pb_base_actual<=0): 						
                        Eb_commitment_battery+= u_remain
                        Eb_d_commitment_battery+= u_remain						
                    elif ((Pb_base_actual>0) and (u_remain<=-Pb_base_actual*P.DT)):
                        Eb_commitment_battery+=u_remain + Pb_base_actual*P.DT
                        Eb_d_commitment_battery+=u_remain + Pb_base_actual*P.DT						
                    u_remain = 0

# above we have used all batteries that FeedAfter and are 'active'.
# if there is remaining commitment, then we need to use all the batteries that FeedAfter and maybe they are not active.

        if (u_remain < 0):		
            Pb_base_actual = Pb_actual		                                   # we update the baseline power to the battery
            if ((FeedAfter_b>0) and (Vd_tmp<0)):                               # we consider the batteries that are going to feed-in energy in the near future
                                											   # using this available discharging potential will not create costs due to differences with the baseline operation of the battery
                tmp = min(-Vd_tmp, FeedAfter_b)                                # > 0
												                               # we would like not to use more flexibility than the FeedAfter, in order not to create any additional costs due to the baseline differences
                if (u_remain <= -tmp): 
                    u_remain += tmp					                           # the remaining commitment is reduced
                    Eb_commitment += -tmp  				                       # we have a negative commitment from the household
                    Eb_d_commitment += -tmp
                    Pb_actual += -tmp / P.DT 				                       # the battery is discharging
                    Vd_tmp += tmp				                               # then the discharging potential is reduced
                    FeedAfter_b = 0

                    if (Pb_base_actual<=0):   				                   # if the battery is currently discharging, any additional commitment will come directly from the battery
                        Eb_commitment_battery+= -tmp		                   # this flexibility comes from the battery
                        Eb_d_commitment_battery+= -tmp						
                    elif ((Pb_base_actual>0) and (tmp>=Pb_base_actual*P.DT)):    # if the battery is currently charging, then part of it will come from the battery and part of it by blocking the current charging
                        Eb_commitment_battery+= tmp - Pb_base_actual*P.DT
                        Eb_d_commitment_battery+= tmp - Pb_base_actual*P.DT				
                else: 
                    Eb_commitment+= u_remain
                    Eb_d_commitment+= u_remain
                    Pb_actual += u_remain / P.DT
                    Vd_tmp+= -u_remain
                    if (Pb_base_actual<=0):						
                        Eb_commitment_battery+= u_remain
                        Eb_d_commitment_battery+= u_remain						
                    elif ((Pb_base_actual>0) and(u_remain<=-Pb_base_actual*P.DT)): 
                        Eb_commitment_battery+= u_remain + Pb_base_actual*P.DT
                        Eb_d_commitment_battery+= u_remain + Pb_base_actual*P.DT						
                    u_remain = 0					
              
        if (u_remain < 0):                                                     # If there is still uncovered commitment, then we go through all the remaining batteries based on the costs of using these batteries
            Pb_base_actual = Pb_actual
            if ((u_remain <= Vd_tmp) and (Vd_tmp<0)): 
                u_remain += -Vd_tmp
                Eb_commitment+= Vd_tmp
                Eb_d_commitment+= Vd_tmp
                Pb_actual+= Vd_tmp/P.DT					
                if (Pb_base_actual <= 0):       					# if the battery is currently discharging, then all the required commitment is taken directly from the battery
                    Eb_commitment_battery+= Vd_tmp
                    Eb_d_commitment_battery+= Vd_tmp
                elif ((Pb_base_actual>0) and (Vd_tmp <= -Pb_base_actual*P.DT)):
                    Eb_commitment_battery+= Vd_tmp+Pb_base_actual*P.DT
                    Eb_d_commitment_battery+= Vd_tmp+Pb_base_actual*P.DT
                Vd_tmp=0
            elif ((u_remain > Vd_tmp) and (Vd_tmp<0)):
                Eb_commitment+= u_remain
                Eb_d_commitment+= u_remain
                Pb_actual+= u_remain / P.DT
                Vd_tmp+= -u_remain					
                if (Pb_base_actual<= 0):
                    Eb_commitment_battery+= u_remain
                    Eb_d_commitment_battery+= u_remain
                elif ((Pb_base_actual>0) and (u_remain <= -Pb_base_actual*P.DT)): 
                    Eb_commitment_battery+= u_remain + Pb_base_actual*P.DT
                    Eb_d_commitment_battery+= u_remain + Pb_base_actual*P.DT
                u_remain = 0	           
    else:
        if (total_commitment == 0): 
            Eb_commitment = 0
            Eb_c_commitment = 0
            Eb_d_commitment = 0
            Eb_commitment_battery = 0
            Eb_c_commitment_battery = 0
            Eb_d_commitment_battery = 0
            Pb_actual = Pb_base_actual		
	
    Pb_c_commitment = Eb_c_commitment_battery / P.DT
    Pb_d_commitment = Eb_d_commitment_battery / P.DT                             # creating power commitments that come directly from the batteries
    Pg = Pb_actual - DP_forecast_day[current_interval_ind]                         # Having computed the power to the battery and the power to the grid (including the activations) we could compute also the expected Next State of the battery at the beginning of the next interval
    Vc_next, Vd_next, SOC_tmp, Pb_baseline_next, Pg_next, Pb_c_max, Pb_d_max = ComputeNextState(Pb_actual,DP_forecast_day[current_interval_ind],SOC_current,c_max,d_max,s_max)
    return Eb_commitment,Eb_c_commitment,Eb_d_commitment,Eb_commitment_battery,Pb_actual,Pb_c_commitment,Pb_d_commitment,Pg,SOC_tmp,Pb_baseline_next,Pg_next,Vd,Vc







