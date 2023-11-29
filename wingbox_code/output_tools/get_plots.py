import matplotlib.pyplot as plt
import os


def get_plots(load_cases):
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
                                        r'wingbox_code\output_data\avl_plots\ ' + ids[id] + '_SUBCASE' + str(idx + 1))
            plt.savefig(path_to_save)