\* distribucion_madera_mulchen *\
Minimize
Costo_Total_Transporte: 3995 x_Plywood_Collipulli_P1
 + 3995 x_Plywood_Collipulli_P2 + 3995 x_Plywood_Collipulli_P3
 + 14238 x_Puerto_Coronel_P1 + 14238 x_Puerto_Coronel_P2
 + 14238 x_Puerto_Coronel_P3 + 17260 x_Puerto_Lirquen_P1
 + 17260 x_Puerto_Lirquen_P2 + 17260 x_Puerto_Lirquen_P3
 + 17586 x_Puerto_San_Vicente_P1 + 17586 x_Puerto_San_Vicente_P2
 + 17586 x_Puerto_San_Vicente_P3 + 14093 x_Reman_Coronel_P1
 + 14093 x_Reman_Coronel_P2 + 14093 x_Reman_Coronel_P3
 + 8071 x_Reman_Los_Angeles_P1 + 8071 x_Reman_Los_Angeles_P2
 + 8071 x_Reman_Los_Angeles_P3
Subject To
Asignacion_Total_P1: x_Plywood_Collipulli_P1 + x_Puerto_Coronel_P1
 + x_Puerto_Lirquen_P1 + x_Puerto_San_Vicente_P1 + x_Reman_Coronel_P1
 + x_Reman_Los_Angeles_P1 = 6928.38
Asignacion_Total_P2: x_Plywood_Collipulli_P2 + x_Puerto_Coronel_P2
 + x_Puerto_Lirquen_P2 + x_Puerto_San_Vicente_P2 + x_Reman_Coronel_P2
 + x_Reman_Los_Angeles_P2 = 9620.31
Asignacion_Total_P3: x_Plywood_Collipulli_P3 + x_Puerto_Coronel_P3
 + x_Puerto_Lirquen_P3 + x_Puerto_San_Vicente_P3 + x_Reman_Coronel_P3
 + x_Reman_Los_Angeles_P3 = 5566.55
Maximo_Plywood_Collipulli_P2: x_Plywood_Collipulli_P2 <= 5000
Maximo_Plywood_Collipulli_P3: x_Plywood_Collipulli_P3 <= 4000
Maximo_Puerto_Coronel_P1: x_Puerto_Coronel_P1 <= 12000
Maximo_Puerto_Coronel_P3: x_Puerto_Coronel_P3 <= 10000
Maximo_Puerto_Lirquen_P2: x_Puerto_Lirquen_P2 <= 8000
Maximo_Puerto_San_Vicente_P2: x_Puerto_San_Vicente_P2 <= 8000
Maximo_Puerto_San_Vicente_P3: x_Puerto_San_Vicente_P3 <= 12000
Maximo_Reman_Coronel_P1: x_Reman_Coronel_P1 <= 8000
Maximo_Reman_Los_Angeles_P1: x_Reman_Los_Angeles_P1 <= 6000
Maximo_Reman_Los_Angeles_P2: x_Reman_Los_Angeles_P2 <= 5000
Minimo_Plywood_Collipulli_P2: x_Plywood_Collipulli_P2 >= 1500
Minimo_Plywood_Collipulli_P3: x_Plywood_Collipulli_P3 >= 1000
Minimo_Puerto_Coronel_P1: x_Puerto_Coronel_P1 >= 1200
Minimo_Puerto_Coronel_P3: x_Puerto_Coronel_P3 >= 1200
Minimo_Puerto_Lirquen_P2: x_Puerto_Lirquen_P2 >= 1500
Minimo_Puerto_San_Vicente_P2: x_Puerto_San_Vicente_P2 >= 1500
Minimo_Puerto_San_Vicente_P3: x_Puerto_San_Vicente_P3 >= 800
Minimo_Reman_Coronel_P1: x_Reman_Coronel_P1 >= 1500
Minimo_Reman_Los_Angeles_P1: x_Reman_Los_Angeles_P1 >= 1300
Minimo_Reman_Los_Angeles_P2: x_Reman_Los_Angeles_P2 >= 1500
Nulo_Plywood_Collipulli_P1: x_Plywood_Collipulli_P1 = 0
Nulo_Puerto_Coronel_P2: x_Puerto_Coronel_P2 = 0
Nulo_Puerto_Lirquen_P1: x_Puerto_Lirquen_P1 = 0
Nulo_Puerto_Lirquen_P3: x_Puerto_Lirquen_P3 = 0
Nulo_Puerto_San_Vicente_P1: x_Puerto_San_Vicente_P1 = 0
Nulo_Reman_Coronel_P2: x_Reman_Coronel_P2 = 0
Nulo_Reman_Coronel_P3: x_Reman_Coronel_P3 = 0
Nulo_Reman_Los_Angeles_P3: x_Reman_Los_Angeles_P3 = 0
End
