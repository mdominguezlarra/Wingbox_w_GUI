
########################################
# WINGBOX ANALYSIS INITIALIZATION FILE #
########################################

# Murilo Caetano da Silva
#           &
# Mikel Dominguez Larrabeiti
#       June 2023

# Run this file once the desired user inputs have been set.

# TIP: If you want to change the number of inputs, loads, or airfoils WITHIN the GUI, make sure to change
#      the values n_sections, n_airfoils, or n_loads beforehand. Otherwise, error warnings will pop up.
#      It is also recommended to change the inputs directly at the 'root', since it is where the validators
#      are applied.


import pandas as pd
import numpy as np
from parapy.gui import display
from wingbox_code.wingbox_assessment import WingBoxAssessment
import warnings
from wingbox_code.format.tk_warn import generate_warning


def appender(data_frame, row_idx, label, type_i, rib_str=False, ):
    """ Extracting the values of a certain parameter along a certain row, giving a warning if the type is wrong
    :param data_frame: Sheet from the input file
    :param row_idx: Row index
    :param label: label of the parameter
    :param type_i: desired parameter type
    :param rib_str: Boolean for certain rows where the first column is blacked out, it also accounts for float inputs
    :return:
    """
    column_idx = 1
    if rib_str:
        column_idx = 2

    input_lst = []
    while data_frame.iloc[row_idx, column_idx] is not np.nan:
        input_lst.append(data_frame.iloc[row_idx, column_idx])
        column_idx = column_idx + 1
        if not isinstance(input_lst[-1], type_i):
            # error message
            msg = 'Wrong input type for {}, correct type is {}'.format(label, type_i)
            warnings.warn(msg)
            generate_warning('Warning: Wrong Input Type', msg)

    return input_lst


def material_name(data_frame, row_idx, label):
    """ Extracting the name of the materials for the wingbox
    :param data_frame: Sheet from the input file
    :param row_idx: Row index
    :param label: Label for the component
    :return:
    """
    column_idx = 1
    material = ''
    warn = False
    msg_m = ''

    if data_frame.iloc[row_idx, 1] not in ['Al2024', 'Al750', 'Al7475']:
        msg_m = 'Material Input A: Invalid material name for {}.'.format(label)
        warn = True

    elif data_frame.iloc[row_idx, 2] not in ['T3', 'T7451', 'T61']:
        msg_m = 'Material Input B:Invalid material temper for {}.'.format(label)
        warn = True

    elif data_frame.iloc[row_idx, 4] not in ['A', 'B', 'S']:
        msg_m = 'Material Input D: Invalid material basis for {}.'.format(label)
        warn = True

    if warn:
        warnings.warn(msg_m)
        generate_warning('Warning: Material', msg_m)

    while data_frame.iloc[row_idx, column_idx] is not np.nan:
        material = material + '-' + str(data_frame.iloc[row_idx, column_idx])
        column_idx = column_idx + 1

    return material[1:]


def coherence_warning(len_input_lst, reference, label, header):
    """Creates a warning in the case that not all of the required inputs have the same size, indicating
    a disparity in sections, cases, or materials
    :param len_input_lst: List of the input lengths
    :param reference: Int which specifies the required length of the inputs
    :param label: Name of the inputs in question
    :param header: Header for the warning
    :return:
    """
    if not set(len_input_lst) == {reference}:
        msg = 'Not all {} have been completely described. Please revise the input file and fill in' \
              ' the missing inputs.'.format(label)
        warnings.warn(msg)
        generate_warning('Warning: {}'.format(header), msg)

    return


def type_warning(value, label, type_i):
    """
    Checks the type of the input and creates a warning if such a type is wrong
    :param value: input in question
    :param label: label for the input
    :param type_i: required type(s)
    :return:
    """
    if not isinstance(value, type_i):
        # error message
        msg = 'Wrong input type for {}, correct type is {}'.format(label, type_i)
        warnings.warn(msg)
        generate_warning('Warning: Wrong Input Type', msg)

    return


#######################################################################################################################
#######################################################################################################################

# Loading the file and arranging the sheets
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
spans = [0] + appender(df_i, 6, 'spans', (float, int))
tapers = [1] + appender(df_i, 7, 'tapers', (float, int))
sweeps = appender(df_i, 8, 'sweeps', (float, int))
dihedrals = appender(df_i, 9, 'dihedrals', (float, int))
incidence = df_i.iloc[3, 1]
twist = [incidence] + appender(df_i, 10, 'twists', (float, int))

# Type check
type_warning(root_chord, 'root chord', (float, int))
type_warning(incidence, 'incidence angle', (float, int))

# Airfoil Placement

airfoil_names_unordered = [str(airfoil) for airfoil in appender(df_i, 19, 'airfoil names', (str, int))]
airfoil_sections_unordered = appender(df_i, 20, 'airfoil positions', (float, int))

airfoil_names = [x for _, x in sorted(zip(airfoil_sections_unordered, airfoil_names_unordered))]
airfoil_sections = sorted(airfoil_sections_unordered)

# Checking for errors

if len(airfoil_names) != len(airfoil_sections):
    # error message
    msg = 'Please input as many airfoil names as spanwise positions.'
    warnings.warn(msg)
    generate_warning('Warning: Airfoils', msg)

n_airfoils = len(airfoil_names)

if (0 or 1) not in airfoil_sections:
    # error message
    msg = 'Either no tip or no root airfoil was input'
    warnings.warn(msg)
    generate_warning('Warning: Root/tip Airfoil', msg)


# Sheet 2
df_i = dfs[1]

# Loading Cases
case_settings = [appender(df_i, 2, 'load case name', str),
                 appender(df_i, 3, 'load case variable', str),
                 appender(df_i, 4, 'load case value', (float, int))]
weight = df_i.iloc[6, 1]
speed = df_i.iloc[7, 1]
height = df_i.iloc[8, 1]

# Type check
type_warning(weight, 'weight', (float, int))
type_warning(speed, 'speed', (float, int))
type_warning(height, 'altitude', (float, int))


# Sheet 3
df_i = dfs[2]

# Structural Geometry
front_spar_loc = appender(df_i, 5, 'front spar positions', float)
rear_spar_loc = appender(df_i, 6, 'rear spar positions', float)
rib_idx = appender(df_i, 7, 'ribs inputs', int, True)

top_stringers = appender(df_i, 8, 'stringer inputs', int, True)
bottom_stringers = appender(df_i, 9, 'stringer inputs', int, True)

if len(top_stringers) == len(bottom_stringers):                # Checking for coherence
    stringer_idx = [[top_stringers[i], bottom_stringers[i]]
                    for i in range(len(top_stringers))]

else:
    stringer_idx = []
    # error message
    msg = 'Number of sections with top and bottom stringers is not coherent. Revise the input file.'
    warnings.warn(msg)
    generate_warning('Warning: Stringer Sections', msg)

TE_skin_gap = df_i.iloc[11, 1]
TE_ribs_gap = df_i.iloc[12, 1]

secs = []

for i in range(3):
    csi = appender(df_i, 15+i, 'cross section', (float, int))
    if len(csi) == 2:
        label = 'dims'
    elif len(csi) == 4:
        label = 'moms'
    else:
        msg = 'Cross-section input ill-posed. Input 2 dimensions of length and width or 4 dimensions of moment' \
              ' of inertia as defined in the input sheet.'
        warnings.warn(msg)
        generate_warning('Warning: Wrong Cross-section Input', msg)
        label = ''
    secs.append([csi, label])

mat_2D = [material_name(df_i, 31, 'skin'),
          material_name(df_i, 27, 'spar web'),
          material_name(df_i, 29, 'rib web')]

mat_1D = [material_name(df_i, 32, 'stringers'),
          material_name(df_i, 28, 'spar caps'),
          material_name(df_i, 30, 'rib caps')]

# Type check
type_warning(TE_ribs_gap, 'rib TE cut', (float, int))
type_warning(TE_skin_gap, 'skin TE cut', (float, int))


# Sheet 4
df_i = dfs[3]

# Mesh Details

bdf_file_path = 'wingbox_code/bdf_files/wingbox_bulkdata.bdf'
if df_i.iloc[6, 1] is not np.nan:
    bdf_file_path = df_i.iloc[6, 1]

tc_select = df_i.iloc[7, 1]
min_elem_size = df_i.iloc[8, 1]
max_elem_size = df_i.iloc[9, 1]
quad_dominance = False

if df_i.iloc[10, 1] == 'Y' or df_i.iloc[10, 1] == 'y':
    quad_dominance = True
elif df_i.iloc[10, 1] != 'N' and df_i.iloc[10, 1] != 'n' and df_i.iloc[10, 1] is not np.NaN:
    msg = 'Input Y, N or leave empty for the quad dominance input to be valid.'
    warnings.warn(msg)
    generate_warning('Warning: Tri or Quad Dominance?', msg)

bcs = []
labels = ['root_rib', 'front_spar', 'rear_spar']

for i in range(3):
    sliced = pd.Index.notna(df_i.iloc[13+i, 1:7])
    dof = ''
    for j in range(6):
        if sliced[j]:
            dof = dof + str(j+1)

    bcs.append([labels[i], dof])

# Checking that all parameters have the correct number of inputs for n sections
# n elements: sweeps, dihedrals, rib_idx, stringer_idx
# n+1 elements : spans, tapers, twist, front_spar_loc, rear_spar_loc

lengths = [len(sweeps), len(dihedrals), len(rib_idx), len(stringer_idx), len(spans)-1, len(tapers)-1,
           len(twist)-1, len(front_spar_loc)-1, len(rear_spar_loc)-1]

coherence_warning(lengths, len(sweeps), 'wing sections', 'Wing Geometry')
n_sections = len(sweeps)

# Checking coherence for the load cases

length_load = [len(i) for i in case_settings]

coherence_warning(length_load, len(case_settings[0]), 'load cases', 'Load Cases')
n_loads = len(case_settings[0])

# Print inputs
# print(root_chord, spans, tapers, sweeps, dihedrals, twist, airfoil_sections, airfoil_names, case_settings, weight,
#       speed, height, rib_idx, front_spar_loc, rear_spar_loc, stringer_idx, TE_ribs_gap, TE_skin_gap,
#       mat_2D, mat_1D)

#######################################################################################################################
#######################################################################################################################

# INITIALIZATION

display(WingBoxAssessment(root_chord=root_chord,
                          n_sections=n_sections,
                          spans=spans,
                          tapers=tapers,
                          sweeps=sweeps,
                          dihedrals=dihedrals,
                          twist=twist,
                          n_airfoils=n_airfoils,
                          airfoil_sections=airfoil_sections,
                          airfoil_names=airfoil_names,
                          n_loads=n_loads,
                          case_settings=case_settings,
                          weight=weight,
                          speed=speed,
                          height=height,
                          rib_idx=rib_idx,
                          front_spar_loc=front_spar_loc,
                          rear_spar_loc=rear_spar_loc,
                          stringer_idx=stringer_idx,
                          TE_ribs_gap=TE_ribs_gap,
                          TE_skin_gap=TE_skin_gap,
                          secs=secs,
                          mat_2D=mat_2D,
                          mat_1D=mat_1D,
                          bdf_file_path=bdf_file_path,
                          min_elem_size=min_elem_size,
                          max_elem_size=max_elem_size,
                          tc_select=tc_select,
                          quad_dominance=quad_dominance,
                          bcs=bcs))
