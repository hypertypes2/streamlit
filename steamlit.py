# -*- coding: utf-8 -*-

import streamlit as st
from collections import defaultdict

cluster_table = [
    [0.37478751, 0.40755565, 0.135777],
    [0.39698932, 0.69913973, 0.13754941],
    [0.47829826, 0.34080224, 0.41514316],
    [0.47503356, 0.66810258, 0.44517527],
    [0.56160588, 0.32664395, 0.70315284],
    [0.52661201, 0.63053157, 0.77400612]
]

norm_table = [[17.5, 41], [27, 95], [0, 15]]
pmv_table = [[0.5, 0.5, 1.0, 1.0, 1.0], [0.0, 0.0, 0.0, 0.0, 0.0], [-1.0, -1.0, -1.0, -0.5, -0.5]]
zone_table = [[3, 3, 5, 2, 4, 1]]
epsilon = 0.01
zone_dict = {1: 3, 2: 3, 3: 5, 4: 2, 5: 4, 6: 1}

def LIMIT(M, N, X):
    if X < M:
        X = M
    elif X > N:
        X = N
    return X

def CalibrateSettingTemp(SetTemp, PmvTemp):
    global pmv_table
    ST = SetTemp * 100
    PT = PmvTemp * 100
    nStep, nCol = 0, 0
    if ST <= 2400:
        nStep = 0
    elif ST <= 2600:
        nStep = 1
        SetTemp = PmvTemp
    elif ST <= 3000:
        nStep = 2
    if PT <= 2400:
        nCol = 0
    elif PT <= 2450:
        nCol = 1
    elif PT <= 2500:
        nCol = 2
    elif PT <= 2550:
        nCol = 3
    elif PT <= 2600:
        nCol = 4
    return SetTemp + pmv_table[nStep][nCol]

def GetTargetTemp(p):
    fHumi = p[1]
    fTemp = p[2]
    if fHumi < 39:
        fRet = 26.0
    elif fHumi < 59:
        fRet = 25.5
    elif fHumi < 81:
        fRet = 25.0
    elif fHumi < 91:
        fRet = 24.5
    else:
        fRet = 24.0
    fRet = LIMIT(24.0, 26.0, fRet)
    fRet = CalibrateSettingTemp(fTemp, fRet)
    return LIMIT(16.0, 30.0, fRet)

def DiffTemp(p):
    diff = abs(p[0] - p[2])
    p.pop()
    p.append(diff)

def Scaling(p):
    global norm_table
    scaled_p = []
    for n in range(3):
        scaled_p.append((p[n] - norm_table[n][0]) / (norm_table[n][1] - norm_table[n][0] + epsilon))
    return scaled_p

def GetCluster(p):
    global cluster_table
    dist = []
    for lv in range(6):
        FD = (p[0] - cluster_table[lv][0]) ** 2 + (p[1] - cluster_table[lv][1]) ** 2 + (p[2] - cluster_table[lv][2]) ** 2
        if (p[0] - cluster_table[lv][0]) * (p[2] - cluster_table[lv][2]) < 0:
            FD += 0.1 * (abs(p[0] - cluster_table[lv][0]) + abs(p[2] - cluster_table[lv][2]))
        dist.append(FD ** 0.5)
    return dist.index(min(dist)) + 1

def simulation(test_case, TC_num, TC_list):
    thermo_on = True
    PMV = GetTargetTemp(test_case)
    if test_case[0] <= PMV:
        thermo_on = False        
    test_case.pop()
    test_case.append(PMV)
    DiffTemp(test_case)
    scaled_p = Scaling(test_case)
    cluster_lv = GetCluster(scaled_p)    
    if not thermo_on:
        TC_list[TC_num].append("THERMO OFF")
    else:
        TC_list[TC_num].append(cluster_lv)
        TC_list[TC_num].append(zone_dict[cluster_lv])
        TC_list[TC_num].append(PMV)

st.title("Smartcare TestCase Simulation")

temp = st.number_input("Input Temperature (C):", min_value=16.0, max_value=30.0, value=26.0,step = 0.5)
humidity = st.number_input("Input Humidity (%):", min_value=0, max_value=100, value=70, step = 1)
target_temp = st.number_input("Input Target Temperature (C):", min_value=16.0, max_value=30.0, value=16.0, step = 0.5)

if st.button("Run Simulation"):
    test_case = [temp, humidity, target_temp]
    TC_result = defaultdict(list)
    TC_num = 1
    simulation(test_case, TC_num, TC_result)
    
    st.write(f"Test Case #{TC_num} Results:")
    
    if TC_result[TC_num]:
        if "THERMO OFF" in TC_result[TC_num]:
            st.write("Thermostat: OFF")
        else:
            cluster_lv = TC_result[TC_num][0]
            zone_lv = TC_result[TC_num][1]
            PMV_temp = TC_result[TC_num][2]
            st.write(f"Cluster Level : {cluster_lv}")
            st.write(f"Comfort Zone : {zone_lv}")
            st.write(f"PMV Temperature : {PMV_temp:.2f}C")
