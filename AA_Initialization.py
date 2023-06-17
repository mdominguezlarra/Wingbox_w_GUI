
########################################
# WINGBOX ANALYSIS INITIALIZATION FILE #
########################################

# Run this file once the desired user inputs have been set


import pandas as pd
from kbeutils import avl
import numpy as np
from parapy.gui import display
from code.wingbox_assessment import WingBoxAssessment


def appender(data_frame, row_idx, rib_str=False):
    column_idx = 1
    if rib_str:
        column_idx = 2

    input_lst = []
    while data_frame.iloc[row_idx, column_idx] is not np.nan:
        input_lst.append(data_frame.iloc[row_idx, column_idx])
        column_idx = column_idx + 1

    return input_lst


def material_name(data_frame, row_idx):
    column_idx = 1
    material = ''
    while data_frame.iloc[row_idx, column_idx] is not np.nan:
        material = material + '-' + str(data_frame.iloc[row_idx, column_idx])
        column_idx = column_idx + 1

    return material[1:]


excel_file = pd.ExcelFile('wingbox_user_inputs.xlsx')
sheet_names = excel_file.sheet_names

df = [None]
dfs = []
for sheet_name in sheet_names:
    df = excel_file.parse(sheet_name)
    dfs.append(df)
    # print(f"Sheet Name: {sheet_name}")
    # print(df)
    # print("\n")

# Sheet 1
df_i = dfs[0]

# Section Geometry

root_chord = df_i.iloc[2, 1]
spans = [0] + appender(df_i, 6)
tapers = [1] + appender(df_i, 7)
sweeps = appender(df_i, 8)
dihedrals = appender(df_i, 9)
twist = [df_i.iloc[3, 1]] + appender(df_i, 10)

# Airfoil Placement

airfoil_names = [str(airfoil) for airfoil in appender(df_i, 16)]
airfoil_sections = appender(df_i, 17)


# Sheet 2
df_i = dfs[1]

# Loading Cases
cases = appender(df_i, 4)
case_settings = []
for i in range(1, len(cases)+1):

    if df_i.iloc[3, i] == 'alpha':
        case_settings.append((df_i.iloc[2, i], {'alpha': cases[i]}))

    elif df_i.iloc[3, i] == 'CL':
        case_settings.append((df_i.iloc[2, i], {'alpha': avl.Parameter(name='alpha',
                                                                       value=cases[i-1],
                                                                       setting=df_i.iloc[2, i])}))

    else:
        print('Wrong alphabetic inputs! Create warning')

weight = appender(df_i, 5)
speed = appender(df_i, 6)
height = appender(df_i, 7)


# Sheet 3
df_i = dfs[2]

# Structural Geometry
front_spar_loc = appender(df_i, 2)
rear_spar_loc = appender(df_i, 3)
rib_idx = appender(df_i, 4, True)

if len(appender(df_i, 5, True)) == len(appender(df_i, 6, True)):
    stringer_idx = [[appender(df_i, 5, True)[i], appender(df_i, 6, True)[i]] for i in range(len(appender(df_i, 5, True)))]

else:
    stringer_idx = []
    print('Number of sections in the stringers not coherent. Make warning')

# str_cs = df_i.iloc[7, 1]      # Placeholder until resolved

TE_skin_gap = df_i.iloc[9, 1]
TE_ribs_gap = df_i.iloc[10, 1]

mat_2D = [material_name(df_i, 25),     # SKIN
          material_name(df_i, 21),     # SPAR WEB
          material_name(df_i, 23)]     # RIB WEB

mat_1D = [material_name(df_i, 26),     # STRINGERS
          material_name(df_i, 22),     # SPAR CAPS
          material_name(df_i, 24)]     # RIB CAPS


# Sheet 4
# df_i = dfs[3]

# INITIALIZATION

display(WingBoxAssessment(root_chord=root_chord,
                          spans=spans,
                          tapers=tapers,
                          sweeps=sweeps,
                          dihedrals=dihedrals,
                          twist=twist,
                          airfoil_sections=airfoil_sections,
                          airfoil_names=airfoil_names,
                          rib_idx=rib_idx,
                          front_spar_loc=front_spar_loc,
                          rear_spar_loc=rear_spar_loc,
                          stringer_idx=stringer_idx,
                          TE_ribs_gap=TE_ribs_gap,
                          TE_skin_gap=TE_skin_gap,
                          mat_2D=mat_2D,
                          mat_1D=mat_1D))
                            # Add remaining inputs

                            # FIX SHEET 2
                            # case_settings = case_settings,
                            # weight = weight[0],
                            # speed = speed[0],
                            # height = height[0],
