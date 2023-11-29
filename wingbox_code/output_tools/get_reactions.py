import os


def get_reactions():
    # Getting general forces and reactions for each case.
    f06_loc = os.path.join(os.getcwd(), r'wingbox_code\output_data\raw_NASTRAN_output\wingbox_bulkdata.f06')
    react_loc = r'wingbox_code\output_data\categorized_outputs\reactions\ '
    totals_lst = []

    with open(f06_loc, 'r') as file:
        for line in file:
            if '             TOTALS' in line:
                totals_lst.append(line)

    totals_lst = totals_lst[0:3]

    for idx, react in enumerate(totals_lst):
        values = react.split()
        label = values[0].strip()
        values = [float(val) for val in values[1:]]
        write_path = os.path.join(os.getcwd(), react_loc + 'reactions_SUBCASE' + str(idx + 1) + '.txt')

        with open(write_path, 'w') as file:
            file.write('THE TOTAL REACTION FORCES OF THE STRUCTURE OF THE WING ARE:\n')
            file.write('FX=' + str(round(-values[0], 3)) + ' N \n')
            file.write('FY=' + str(round(-values[1], 3)) + ' N \n')
            file.write('FZ=' + str(round(-values[2], 3)) + ' N \n')
            file.write('MX=' + str(round(-values[3], 3)) + ' Nm \n')
            file.write('MY=' + str(round(-values[4], 3)) + ' Nm \n')
            file.write('MZ=' + str(round(-values[5], 3)) + ' Nm \n')