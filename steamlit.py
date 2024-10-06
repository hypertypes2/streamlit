# -*- coding: utf-8 -*-

import streamlit as st
import random
from collections import defaultdict
import matplotlib.pyplot as plt

cluster_table = [
    [0.38605189, 0.42725575, 0.10643174],
    [0.43716458, 0.70885274, 0.13850524],
    [0.51310398, 0.3739555 , 0.34666371],
    [0.54387924, 0.68104063, 0.42058288],
    [0.63436022, 0.34302273, 0.63279737],
    [0.63024018, 0.62681872, 0.74968306]
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
        # if (p[0] - cluster_table[lv][0]) * (p[2] - cluster_table[lv][2]) < 0:
        #     FD += 0.1 * (abs(p[0] - cluster_table[lv][0]) + abs(p[2] - cluster_table[lv][2]))
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

def TestPlot(SetTemp):
    TC_result = defaultdict(list)
    cases = defaultdict(list)
    N = 1000
    for i in range(N):
        # random.randrange() :  int
        Temp = round(random.uniform(17.5,41),1)
        Hum = round(random.uniform(27,95),0)
        test = [Temp,Hum,SetTemp]  
        for inputs in test:
            cases[i+1].append(inputs)
       
        simulation(test, i+1, TC_result)
       
    for n in range(1,N+1):
        for i in range(len(TC_result[n])):
            cases[n].append(TC_result[n][i])
           
    plt.figure(figsize=(5,3))
    plt.title(f"set temp : {SetTemp}")
    for i in range(1,len(cases)+1):
        if cases[i][3] == 'THERMO OFF':
            continue
        plt.scatter(cases[i][0],cases[i][3])
    plt.ylabel("cluster Lv")
    plt.xlabel("current temp")
    plt.grid(True)
    plt.xticks(range(17,41,2))
    #plt.show()
    
    # Show the plot in Streamlit
    st.pyplot(plt)

st.title("Smartcare TestCase Simulation")

# Create tabs for simulation and plotting
tab1, tab2 = st.tabs(["Run Simulation", "Generate Simulation"])


with tab1:
    temp = st.number_input("Input Temperature (C):", min_value=16.0, max_value=30.0, value=25.0, step=0.5)
    humidity = st.number_input("Input Humidity (%):", min_value=0, max_value=100, value=50, step=1)
    target_temp = st.number_input("Input Target Temperature (C):", min_value=16.0, max_value=30.0, value=18.0, step=0.5,key='tab1')
    if st.button("Run Simulation"):
        test_case = [temp, humidity, target_temp]
        TC_result = defaultdict(list)
        TC_num = 1
        simulation(test_case, TC_num, TC_result)
        
        st.subheader("Test Case Results")
        
        if TC_result[TC_num]:
            if "THERMO OFF" in TC_result[TC_num]:
                st.write("Thermo OFF")
            else:
                cluster_lv = TC_result[TC_num][0]
                zone_lv = TC_result[TC_num][1]
                PMV_temp = TC_result[TC_num][2]
                st.write(f"Cluster Level : {cluster_lv}")
                st.write(f"Comfort Zone : {zone_lv}")
                st.write(f"PMV Temperature : {PMV_temp:.1f} C")

with tab2:
    target_temp = st.number_input("Input Target Temperature (C):", min_value=16.0, max_value=30.0, value=18.0, step=0.5, key='tab2')

    if st.button("Generate Plot"):
        with st.spinner("Generating plot..."):
            TestPlot(target_temp)  # target_temp만 전달

