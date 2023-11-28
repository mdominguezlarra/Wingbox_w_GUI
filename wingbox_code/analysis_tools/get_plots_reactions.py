import matplotlib.pyplot as plt
import os


def get_plots_reactions(load_cases):
    for idx, case in enumerate(load_cases):
        ids = ['L', 'D', 'M']
        L_vec = [load[0] for load in case.forces_moms]
        D_vec = [load[1] for load in case.forces_moms]
        M_vec = [load[2] for load in case.forces_moms]
        F_vec = [L_vec, D_vec, M_vec]
        y_vec = [pos[1] for pos in case.forces_moms_pos]

        # Plotting and saving.
        px = 1 / plt.rcParams['figure.dpi']
        for id, vec in enumerate(F_vec):
            plt.figure(figsize=(800 * px, 600 * px))
            plot_handle = plt.plot(y_vec, vec)
            plt.grid(True)
            plt.xlabel('y [m]')
            plt.ylabel(ids[id] + ' [N]')
            path_to_save = os.path.join(os.getcwd(),
                                        r'wingbox_code\output_data\avl_plots\ ' + ids[id] + '_case_' + str(idx + 1))
            plt.savefig(path_to_save)

    # Getting general forces and reactions for each case.
    f06_loc = os.path.join(os.getcwd(), r'wingbox_code\output_data\wingbox_bulkdata.f06')
    react_loc = r'wingbox_code\output_data\react_forces_moms\ '
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
        write_path = os.path.join(os.getcwd(), react_loc + 'react_SUBCASE' + str(idx + 1) + '.txt')

        with open(write_path, 'w') as file:
            file.write('THE TOTAL REACTION FORCES OF THE STRUCTURE OF THE WING ARE:\n')
            file.write('FX=' + str(round(values[0], 3)) + ' N \n')
            file.write('FY=' + str(round(values[1], 3)) + ' N \n')
            file.write('FZ=' + str(round(values[2], 3)) + ' N \n')
            file.write('MX=' + str(round(values[3], 3)) + ' Nm \n')
            file.write('MY=' + str(round(values[4], 3)) + ' Nm \n')
            file.write('MZ=' + str(round(values[5], 3)) + ' Nm \n')