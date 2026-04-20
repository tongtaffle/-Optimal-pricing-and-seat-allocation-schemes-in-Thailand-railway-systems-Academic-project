# -*- coding: utf-8 -*-
"""
Created on Thu Mar 13 19:00:29 2025

@author: User
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Mar 11 14:41:16 2025

@author: User
"""
import pandas as pd
import random
import numpy as np
import math
from collections import defaultdict

### set parameter ###
T0=100
Tmin=50
I1=10
I2=5
alpha=0.5
Beta=[0.56,0.6,0.64,0.68,0.72,0.76,0.8,0.84,0.88,0.92,0.96,1]
eta = [1.8, 1.4, 1.2, 0.8]
theta = 0.012


### Fuction : Determine Z ###
def calculate_Z(y, p, z, x, v, K, L, W):
    # First component
    component1 = 0.6 * sum(
        y[l][(r,s)][k] * p[l][(r,s)] * z[l][(r,s)][k]
        for l in L
        for (r,s) in W
        for k in range(1, K + 1)
    )

    # Second component
    component2 = -0.4 * v * sum(
        z[l][(r,s)][k] * sum(
            x[l][stations[n]]
            for n in range(stations.index(r)+1,stations.index(s))
        )
        for k in range(1, K + 1)
        for l in L
        for (r, s) in W
    )

    return component1 + component2

 ### Fuction : Constraints ###
def check_constraints(x, y, z, qklrs, phi, f, R, L, W, K, constraint_stations, station_index, constraint_station_index):
    # 1. Price constraints
    for l in L:
        for (r, s) in W:
            for k in range(1, K + 1):
                if y[l][(r, s)][k] <= 0:
                    return False, f"Price constraint violated: y_{l}_{r}_{s} <= 0"

            for k in range(2, K + 1):
                if y[l][(r, s)][k - 1] > y[l][(r, s)][k]:
                    return False, f"Ticket price increase constraint violated: y_{l}_{r}_{s} at period {k-1} > y_{l}_{r}_{s} at period {k}"

    # 2. Ticket constraints (12)
    for l in L:
        for (r, s) in W:
            for k in range(1, K + 1):
                if not isinstance(z[l][(r, s)][k], int):
                    return False, f"Ticket constraint violated: z_{l}_{r}_{s} is not an integer"

                # Ticket constraints (13)
                if (x[l][r]*x[l][s]-1)*z[l][(r,s)][k] != 0:
                   service_found = False
                   for l_other in L:
                       if l_other != l and x[l_other][r] == 1 and x[l_other][s] == 1:
                            service_found = True
                            break
                if not service_found:
                    return False, f"Train on line {l} must allocate tickets to OD ({r},{s}) if it serves both stations."

    # 2.1 Rejected passenger (15)
    for l in L:
        for (r, s) in W:
            for k in range(1, K + 1):
                if z[l][(r, s)][k] > qklrs[l][(r,s)][k] + R[l][(r,s)][k]:
                    return False, f"Ticket allocation constraint violated: z_{l}_{r}_{s}_{k} > q_{l}_{r}_{s}_{k} + r_{l}_{r}_{s}_{k}"

    # 3. Capacity constraint (16) and adjustment (24)
    for l in L:
        for j in constraint_stations:  
            j_index = constraint_station_index[j]
            sum_tickets = sum(
                z[l][(r, s)][k] 
                for k in range(1, K + 1) 
                for r in stations if station_index[r] <= j_index
                for s in stations if station_index[s] > j_index
            )
    
            # Verify Ticket
            if sum_tickets > 76:
                # Compute by equation (16)
                denominator = sum(
                    qklrs[l][(r, s)][k] 
                    for k in range(1, K + 1) 
                    for r in stations if station_index[r] <= j_index
                    for s in stations if station_index[s] > j_index
                )
    
    
                # Adjust z by (24)
                for k in range(1, K + 1):
                    for r in stations:
                        for s in stations:
                            if station_index[r] <= j_index and station_index[s] > j_index:
                                z[l][(r, s)][k] = int(qklrs[l][(r, s)][k] * (76 / denominator))
    
                print(f"Capacity constraint violated at station {j}. Adjusted seat allocation.")
                    

    # 5. Reachability constraints (17)
    for (r, s) in W:
        if sum(x[l][r] * x[l][s] for l in L) < 1:
            return False, f"Reachability constraint violated: No trains can serve OD pair {r}-{s}"
    return True, "All constraints satisfied"

### Fuction : Accept solution ###
def accept_solution(Z_prime_prime, Z_prime, t):
    # Check if Z(S'') >= Z(S')
    if Z_prime_prime >= Z_prime:
        return True
    else:
        # Calculate the probability of accepting a worse solution
        probability = math.exp(-(Z_prime - Z_prime_prime) / t)
        # Generate a random number rho from the interval (0, 1)
        rho = random.uniform(0, 1)
        # Check if rho <= exp(-(Z(S') - Z(S'')) / t)
        if rho <= probability:
            return True
        else:
            return False

### Function: Convert to matrix ###
def convert_to_matrix(x):
    # Create an empty matrix to store the values
    matrix = []

    # Define the order of the columns
    columns_order = ['BKK', 'Yomarat', 'Rama Hospital', 'Sam sen', 'Bang sue', 'DON MUENG', 'Rangsit', 'Klong Nueng', 'Chiang rak', 'TU', 'Navanakhon', 'Chiang rak noi', 'Khlong Phutsa', 'Bang pa in', 'Ayutthaya', 'Ban pa chi']

    # Iterate over the dictionary keys
    for key in x:
        row = []
        # Iterate over the columns order
        for col in columns_order:
            # Append the value to the row
            row.append(x[key][col])
        # Append the row to the matrix
        matrix.append(row)

    return matrix

### Function: Convert to x ###
def convert_to_x(matrix, L):
    columns_order = ['BKK', 'Yomarat', 'Rama Hospital', 'Sam sen', 'Bang sue', 'DON MUENG', 'Rangsit', 'Klong Nueng', 'Chiang rak', 'TU', 'Navanakhon', 'Chiang rak noi', 'Khlong Phutsa', 'Bang pa in', 'Ayutthaya', 'Ban pa chi']
    x = {}
    for i, key in enumerate(L):
        row = matrix[i]
        x[key] = {col: val for col, val in zip(columns_order, row)}
    return x

### Function: Outerneighborhood ###
def outerneighborhood(c_stopplan):
    Coin = ['head', 'tail']
    Selected_coin = random.choice(Coin)
    print(Selected_coin)
    if Selected_coin == 'head':
        ##Selected neighborhood stop plan
        selected_trainstop1 = random.choice(c_stopplan)
        indexstopplan = c_stopplan.index(selected_trainstop1)
        # Choose position in new list
        position = list(range(len(selected_trainstop1)))  # Initialize position list
        n = random.choice(position)
        position.remove(n)  # Update position
        m = random.choice(position)
        # Check index
        while selected_trainstop1[n] == selected_trainstop1[m] and selected_trainstop1 != c_stopplan[7]:
            m = random.choice(position)
        # set variable (for easily reading)
        index1 = selected_trainstop1[n]
        index2 = selected_trainstop1[m]
        # change and create neighborhood stop plan
        selected_trainstop1[n] = index2
        selected_trainstop1[m] = index1
        c_stopplan[indexstopplan] = selected_trainstop1
    else:
        # random train
        train = list(range(len(c_stopplan)))
        n = random.choice(train)
        train.remove(n)
        m = random.choice(train)
        # set train variable
        train_n = c_stopplan[n]
        train_m = c_stopplan[m]
        # Position stop in train
        position = list(range(len(train_n)))  # Initialize position list
        stop_n = random.choice(position)  # 1 or 0
        stop_m = random.choice(position)  # 1 or 0
        # choose same stop
        while train_n[stop_n] != train_m[stop_m]:
            stop_m = random.choice(position)

        # Set variable index in train n and  train m
        index_n = train_n[stop_n]
        index_m = train_m[stop_m]
        # Change and form neighborhood stop plan
        if index_n == 1:
            train_n[stop_n] = 0
            train_m[stop_m] = 0
            c_stopplan[n] = train_n
            c_stopplan[m] = train_m
        else:
            train_n[index_n] = 1
            train_m[index_m] = 1
            c_stopplan[n] = train_n
            c_stopplan[m] = train_m
    print(c_stopplan)
    return c_stopplan

### Function: Inner neighborhood ###
def inner_neighborhood(y, Beta, L, K, W, p, x, eta, theta, t, v, z):
        
    while True:
        # Randomly choose a value for k from K
        random_k = random.randint(1, K)

        # Randomly select a line
        random_line = random.choice(L)

        # Randomly select a station pair (r, s) from W
        random_station_pair = random.choice(W)

        # Randomly select a value for yklrs for the selected k
        yklrs_k = y[random_line][random_station_pair][random_k]

        # Find the values of yklrs for k-1 and k+1
        yklrs_k_minus_1 = y[random_line][random_station_pair][random_k - 1] if random_k > 1 else 0
        yklrs_k_plus_1 = y[random_line][random_station_pair][random_k + 1] if random_k < K else 1

        # Choose Beta_prime from Beta such that yklrs_k_minus_1 <= Beta_prime <= yklrs_k_plus_1
        valid_beta_range = [beta for beta in Beta if yklrs_k_minus_1 <= beta <= yklrs_k_plus_1]
        beta_prime = random.choice(valid_beta_range)

        # Update yklrs with Beta_prime
        y[random_line][random_station_pair][random_k] = beta_prime

        ## Formula (1) ##
        pklrs = {}
        for l in L:
            pklrs[l] = {}
        for (r, s) in W:
            for l in L:
                if (r, s) not in pklrs[l]:
                    pklrs[l][(r, s)] = {}
                for k in range(1, K + 1):
                    pklrs[l][(r, s)][k] = y[l][(r, s)][k] * p[l][(r, s)]

        ## Formula (2) ##
        cklrs = {}
    
        for l in L:
            cklrs[l] = {}
        for (r, s) in W :
            for l in L:
                if (r, s) not in cklrs[l]:
                    cklrs[l][(r, s)] = {}
                for k in range (1, K + 1):
                    cklrs[l][(r , s)][k] = pklrs[l][(r, s)][k] + v

        ## Formula (3) ##
        ckrs = {}

        epsilon = 1e-10  # Small positive value to prevent division by zero

        for (r, s) in W:
            ckrs[(r, s)] = {}
        
            # Compute denominator
            denominator = sum(x[l][r] * x[l][s] for l in L)
            
            # Prevent zero division by ensuring denominator is at least epsilon
            if abs(denominator) < epsilon:
                denominator = epsilon  # Assign a small nonzero value
        
            for k in range(1, K + 1):
                numerator = sum(cklrs[l][(r, s)][k] * x[l][r] * x[l][s] for l in L)
                
                # Compute ckrs ensuring denominator is never zero
                ckrs[(r, s)][k] = numerator / denominator

        ## Formula (4) ##
        pk0lrs = {}
        for l in L:
            pk0lrs[l] = {}
            for (r, s) in W:
                if (r, s) not in pk0lrs[l]:
                    pk0lrs[l][(r, s)] = {}
                pk0lrs[l][(r,s)] = p[l][(r,s)]

        ck0lrs = {}
        for l in L:
            ck0lrs[l] = {}
            for (r, s) in W:
                if (r, s) not in ck0lrs[l]:
                    ck0lrs[l][(r, s)] = {}
                ck0lrs[l][(r, s)] = pk0lrs[l][(r, s)] + v

        ck0rs = {}
        epsilon = 1e-10  # Add small value
        
        for (r, s) in W:
            if (r, s) not in ck0rs:
                ck0rs[(r, s)] = {}
        
            # Compute denominator0
            denominator0 = sum(x[l][r] * x[l][s] for l in L)
        
            # Prevent division by 0
            if abs(denominator0) < epsilon:
                denominator0 = epsilon  
        
            # Compute numerator0
            numerator0 = sum(ck0lrs[l][(r, s)] * x[l][r] * x[l][s] for l in L)
        
            # Compute ck0rs
            ck0rs[(r, s)] = numerator0 / denominator0
        
        qk0rs = {}
        for (r, s) in W:
            if (r, s) not in qk0rs:
                qk0rs[(r, s)] = {}
            #Compute qk0rs(ck0rs)
            qk0rs[(r, s)] = 76* np.exp(0.02 * ck0rs[(r, s)])
        
        qkrs = {}
        for (r, s) in W:
            if (r, s) not in qkrs:
                qkrs[(r,s)] = {}
                   
            for k in range(1, K + 1):
                if ck0rs[(r,s)] > 0:  # Prevent divided by 0
                    ratio = ckrs[(r,s)][k] / ck0rs[(r,s)]
                    exponentpart = -eta[k - 1] * (ratio - 1)
                    qkrs[(r,s)][k] = qk0rs[(r, s)] * np.exp(exponentpart)
                else:
                    qkrs[(r,s)][k] = 0  # no travel cost , passenger demand should be 0
                    
        # Formula 5 Compute phi
        phi = {}
        for l in L:
            phi[l] = {}
            for (r, s) in W:
                if (r, s) not in phi[l]:
                    phi[l][(r, s)] = {}
        
                for k in range(1, K + 1):
                        numerator_phi = np.exp(-theta * cklrs[l][(r,s)][k])
                        denominator_phi = sum(
                            np.exp(-theta * cklrs[lprime][(r,s)][k])
                            for lprime in L )
                        phi[l][(r,s)][k] = numerator_phi / denominator_phi
                   

        # Formula 6 Compute qklrs
        qklrs = {}
        for l in L:
            qklrs[l] = {}
            for (r, s) in W:
                if (r, s) not in qklrs[l]:
                    qklrs[l][(r, s)] = {}
           
                for k in range(1, K + 1):
                    qklrs[l][(r, s)][k] = qkrs[(r,s)][k] * phi[l][(r,s)][k]
                    z[l][(r,s)][k] = int(qklrs[l][(r,s)][k])
            
        #Extra Compute f
        f = {}
        for l in L:
            f[l] = {}
            for (r, s) in W:
                if (r, s) not in f[l]:
                    f[l][(r,s)] = {}
                for k in range(1, K + 1):
                    if k > 1 :
                        f[l][(r,s)][k] = qklrs[l][(r,s)][k] - z[l][(r,s)][k]
                    else:
                        f[l][(r,s)][k] = 0
        #Extra Compute R
        R = {}
        for l in L:
            R[l] = {}
            for (r,s) in W:
                if (r,s) not in R[l]:
                    R[l][(r,s)] = {}
                R[l][(r,s)] = {}
                for k in range(1, K + 1):
                    if k > 1:
                        R[l][(r,s)][k] = f[l][(r,s)][k-1]*phi[l][(r,s)][k]
                    else :
                        R[l][(r,s)][k] = 0
        
        check_constraints(x, y, z, qklrs, phi, f, R, L, W, K, constraint_stations, station_index, constraint_station_index) 
        
        return qk0rs, R, f, qklrs, phi, qkrs, ck0rs, ck0lrs, pk0lrs, ckrs, cklrs, pklrs, z , check_constraints(x, y, z, qklrs, phi, f, R, L, W, K, constraint_stations, station_index, constraint_station_index) 

### Function: Check reachbility constraints ###
def check_reachability_constraints(c_stopplan):
    conditions = []
    for i in range(len(c_stopplan[0])):
        for j in range(i + 1, len(c_stopplan[0])):
            condition = [c_stopplan[k][i] * c_stopplan[k][j] for k in range(len(c_stopplan))]
            conditions.append(condition)

    while True:
        for condition in conditions:
            condition_sum = sum(condition)
            if condition_sum < 1:
                print(f"Condition {condition} is not satisfied: {condition_sum} < 1")    
                # Call outerneighborhood again if condition is not satisfied
                return outerneighborhood(c_stopplan)
        else:
            break

    print("All conditions are satisfied.")
    return True

## INPUT DATA ##
v = 3.1  
K = 4 
L = ['303','339','201','209','233','211','207','301','341','317','313']

stations=['BKK','Yomarat','Rama Hospital','Sam sen','Bang sue',
'DON MUENG','Rangsit','Klong Nueng','Chiang rak','TU','Navanakhon'
,'Chiang rak noi','Khlong Phutsa','Bang pa in','Ayutthaya','Ban pa chi']
constraint_stations = ['BKK', 'Yomarat', 'Rama Hospital', 'Sam sen', 'Bang sue',
'DON MUENG', 'Rangsit', 'Klong Nueng', 'Chiang rak', 'TU',
'Navanakhon', 'Chiang rak noi', 'Khlong Phutsa', 'Bang pa in','Ayutthaya']  
station_index = {station: idx + 1 for idx, station in enumerate(stations)}
constraint_station_index = {station: idx + 1 for idx, station in enumerate(constraint_stations)}

W = [(stations[i], stations[j]) for i in range(len(stations)) for j in range(i+1, len(stations))]
y = {l: {
        (r,s): {1: 0.6, 2: 0.7, 3: 0.8, 4: 0.9}  # Values for k = 1 and k = 2
            for r,s in W
        }
        for l in L}
p = {
    l: {
        (r,s) : 
            30 if stations.index(s) - stations.index(r) == 1 else
            40 if 2 <= stations.index(s) - stations.index(r) <= 6 else
            50 if 7 <= stations.index(s) - stations.index(r) <= 10 else
            60 if 11 <= stations.index(s) - stations.index(r) <= 13 else
            70
            for  r,s in W
        }
        for l in L}

z = {
    l: {
        (r, s) : {1: 19, 2: 19, 3: 19, 4: 19}
                  for r, s in W
    }
    for l in L}

x = { '303': {
    'BKK': 1,
    'Yomarat': 0,
    'Rama Hospital': 0,
    'Sam sen': 1,
    'Bang sue': 1,
    'DON MUENG': 1,
    'Rangsit': 1,
    'Klong Nueng': 0,
    'Chiang rak': 1,
    'TU': 0,
    'Navanakhon': 0,
    'Chiang rak noi': 1,
    'Khlong Phutsa': 1,
    'Bang pa in': 1,
    'Ayutthaya': 1,
    'Ban pa chi': 1 },
    '339': {'BKK': 1,  
    'Yomarat': 0,
    'Rama Hospital': 0,
    'Sam sen': 1,
    'Bang sue': 1,
    'DON MUENG': 1,
    'Rangsit': 1,
    'Klong Nueng': 0,
    'Chiang rak': 1,
    'TU': 1,
    'Navanakhon': 1,
    'Chiang rak noi': 1,
    'Khlong Phutsa': 1,
    'Bang pa in': 1,
    'Ayutthaya': 1,
    'Ban pa chi': 1},
    '201': {'BKK': 1,
    'Yomarat': 0,
    'Rama Hospital': 0,
    'Sam sen': 1,
    'Bang sue': 1,
    'DON MUENG': 1,
    'Rangsit': 1,
    'Klong Nueng': 0,
    'Chiang rak': 1,
    'TU': 1,
    'Navanakhon': 0,
    'Chiang rak noi': 1,
    'Khlong Phutsa': 1,
    'Bang pa in': 1,
    'Ayutthaya': 1,
    'Ban pa chi': 1 },
    '209': {'BKK': 1, 
    'Yomarat': 0,
    'Rama Hospital': 0,
    'Sam sen': 1,
    'Bang sue': 1,
    'DON MUENG': 1,
    'Rangsit': 1,
    'Klong Nueng': 0,
    'Chiang rak': 1,
    'TU': 1,
    'Navanakhon': 0,
    'Chiang rak noi': 1,
    'Khlong Phutsa': 1,
    'Bang pa in': 1,
    'Ayutthaya': 1,
    'Ban pa chi': 1 },
    '233': {'BKK': 1,  
    'Yomarat': 0,
    'Rama Hospital': 1,
    'Sam sen': 1,
    'Bang sue': 1,
    'DON MUENG': 1,
    'Rangsit': 1,
    'Klong Nueng': 0,
    'Chiang rak': 0,
    'TU': 0,
    'Navanakhon': 0,
    'Chiang rak noi': 1,
    'Khlong Phutsa': 0,
    'Bang pa in': 1,
    'Ayutthaya': 1,
    'Ban pa chi': 1 },
    '211': {'BKK': 1,  
    'Yomarat': 0,
    'Rama Hospital': 1,
    'Sam sen': 1,
    'Bang sue': 1,
    'DON MUENG': 1,
    'Rangsit': 1,
    'Klong Nueng': 0,
    'Chiang rak': 0,
    'TU': 0,
    'Navanakhon': 0,
    'Chiang rak noi': 0,
    'Khlong Phutsa': 0,
    'Bang pa in': 1,
    'Ayutthaya': 1,
    'Ban pa chi': 1 },
    '207': {'BKK': 1, 
    'Yomarat': 0,
    'Rama Hospital': 1,
    'Sam sen': 1,
    'Bang sue': 1,
    'DON MUENG': 1,
    'Rangsit': 1,
    'Klong Nueng': 0,
    'Chiang rak': 1,
    'TU': 1,
    'Navanakhon': 0,
    'Chiang rak noi': 1,
    'Khlong Phutsa': 1,
    'Bang pa in': 1,
    'Ayutthaya': 1,
    'Ban pa chi': 1 },
    '301':{'BKK': 1,  
    'Yomarat': 1,
    'Rama Hospital': 1,
    'Sam sen': 1,
    'Bang sue': 1,
    'DON MUENG': 1,
    'Rangsit': 1,
    'Klong Nueng': 1,
    'Chiang rak': 1,
    'TU': 1,
    'Navanakhon': 1,
    'Chiang rak noi': 1,
    'Khlong Phutsa': 1,
    'Bang pa in': 1,
    'Ayutthaya': 1,
    'Ban pa chi': 1 },
    '341': {'BKK': 1,  
    'Yomarat': 1,
    'Rama Hospital': 1,
    'Sam sen': 1,
    'Bang sue': 1,
    'DON MUENG': 1,
    'Rangsit': 1,
    'Klong Nueng': 0,
    'Chiang rak': 1,
    'TU': 1,
    'Navanakhon': 1,
    'Chiang rak noi': 1,
    'Khlong Phutsa': 1,
    'Bang pa in': 1,
    'Ayutthaya': 1,
    'Ban pa chi': 1 },
    '317': {'BKK': 1, 
    'Yomarat': 1,
    'Rama Hospital': 1,
    'Sam sen': 1,
    'Bang sue': 1,
    'DON MUENG': 1,
    'Rangsit': 1,
    'Klong Nueng': 1,
    'Chiang rak': 1,
    'TU': 0,
    'Navanakhon': 0,
    'Chiang rak noi': 1,
    'Khlong Phutsa': 1,
    'Bang pa in': 1,
    'Ayutthaya': 1,
    'Ban pa chi': 1 },
    '313':{'BKK': 1,  
    'Yomarat': 1,
    'Rama Hospital': 1,
    'Sam sen': 1,
    'Bang sue': 1,
    'DON MUENG': 1,
    'Rangsit': 1,
    'Klong Nueng': 1,
    'Chiang rak': 1,
    'TU': 0,
    'Navanakhon': 1,
    'Chiang rak noi': 1,
    'Khlong Phutsa': 1,
    'Bang pa in': 1,
    'Ayutthaya': 1,
    'Ban pa chi': 1 }
}
tlrs = {l: { (r,s): 1 for r,s in W } for l in L}

## Implementation Process
# Step 1: Initialization
# Call the function to convert x to matrix format
c_stopplan = convert_to_matrix(x)
# Initialization of current temperature, current iteration number, and best solution
T = T0
i = i_prime = 1
S_bar = S_best = (x, y, z)
Z_bar = Z_best = calculate_Z(y, p, z, x, v, K, L, W)  # Best objective function value
unchanged_count = 0
print("Value of Z:", Z_best)

while True:  # Loop step 2 - step 6
    # Step 2: Construction of the outer neighborhood solution
    neighborhood_stop_plan = outerneighborhood(c_stopplan)
    check_reachability_constraints(neighborhood_stop_plan)

    # Step 3.1: Obtain the initial solution of the inner layer
    while True:
        x_prime = convert_to_x(neighborhood_stop_plan, L)
        qk0rs, R, f, qklrs, phi, qkrs, ck0rs, ck0lrs, pk0lrs, ckrs, cklrs, pklrs, z_prime, is_valid = inner_neighborhood(y, Beta, L, K, W, p, x_prime, eta, theta, T, v, z)
        validation, message = is_valid
        
        if validation:
            Z_prime = calculate_Z(y, p, z_prime, x_prime, v, K, L, W)
            S_prime = (x_prime, y, z_prime)
            print("Value of Z' after updating y with beta_prime:", Z_prime)
            break  
        else:
            print("Invalid solution:", message)

    # Step 3.2: Construction of the inner neighborhood solution
    i_prime = 1  
    while i_prime <= I1:
        qk0rs, R, f, qklrs, phi, qkrs, ck0rs, ck0lrs, pk0lrs, ckrs, cklrs, pklrs,z_prime_prime, is_valid2 = inner_neighborhood(y, Beta, L, K, W, p, x_prime, eta, theta, T, v, z_prime)
        validation2, message2 = is_valid2
        
        if validation2:
            Z_prime_prime = calculate_Z(y, p, z_prime_prime, x_prime, v, K, L, W)
            S_prime_prime = (x_prime, y, z_prime_prime)
            print("Value of Z'' after updating y with beta_prime:", Z_prime_prime)

            # Step 3.3: Metropolis criterion test for the inner layer
            if Z_prime_prime >= Z_prime:
                S_prime = S_prime_prime
                Z_prime = Z_prime_prime
                print("Accepted new solution (S''), Z_prime_prime:", Z_prime_prime)
            else:
                r = random.uniform(0, 1)
                probability = math.exp((Z_prime - Z_prime_prime) / T)
                
                if r <= probability:
                    S_prime = S_prime_prime
                    Z_prime = Z_prime_prime
                    print("Accepted new solution (S'') by Metropolis criterion, Z_prime_prime:", Z_prime_prime)
                else:
                    print("Rejected new solution (S''), keeping current solution S0, Z_prime:", Z_prime)

            # Step 3.4: Iteration times test for the inner layer
            if i_prime < I1:
                i_prime += 1
                print(f"Iteration {i_prime} complete. Returning to Step 3.2.")
            else:
                print("Iteration limit reached. Outputting solution S' and moving to Step 4.")
                break
        else:
            print("Invalid solution:", message2)

    # Step 4: Metropolis criterion test for the outer layer
    if Z_prime >= Z_best:
        S_bar = S_prime
        Z_bar = Z_prime
        if S_best == S_prime:
            unchanged_count += 1  # Count S_bar unchange
        else:
            unchanged_count = 0  # reset count S_bar change
        S_best = S_prime
        Z_best = Z_prime
    else:
        ro = random.uniform(0, 1)
        delta_Z = (Z_best - Z_prime) / T
        probability2 = math.exp(delta_Z) if -700 < delta_Z < 700 else (1.0 if delta_Z > 700 else 0.0)
        
        if ro <= probability2:
            S_best = S_prime
            Z_best = Z_prime
            unchanged_count = 0  # รีเซ็ตตัวนับถ้า S_best มีการเปลี่ยนแปลง
            print("Accepted new solution (S') by Metropolis criterion, Z_prime:", Z_prime)
        else:
            print("Rejected new solution (S'), keeping current solution S0, Z_prime:", Z_best)

    # Step 5: Iteration number test for the outer layer
    i += 1
    if i >= I2:
        T *= alpha  # decrese temp
        i = 1  # Reset outer iteration
        print("Iteration limit reached for outer layer. Updating temperature and moving to Step 6.")

        # Step 6: Termination check
        if T < Tmin or unchanged_count >= T:
            print(f"Termination condition met. Outputting the best solution found, Z_best: {Z_bar}")
            break  # End
        else:
            print("Continuing with new temperature. Resetting i and returning to Step 2.")
            continue  # Back to Step 2
    else:
        print(f"Outer iteration {i} complete. Returning to Step 2.")