import csv
import os


class AddMaterial:
    """
    Adds a new material to the .csv material input file. Standardized to accept metals only.
    Suggested reference: MIL-HDBK-5J.

    """

    def __init__(self, spec: str, name: str, temper: str, t: list, basis: str, E_vector:list, G, nu, sigma: list, units='imperial', rho=5.2388):
        self.id = [spec, name, temper, basis]
        self.t = t
        self.mech_props = [E_vector[0], E_vector[1], G, nu, rho]
        self.sigma = sigma
        self.units = units

    def append_to_csv(self):
        """
        Appends the created material to the .csv input file.
        Creates a .csv input file if none exist in the current folder.
        """

        # Creation of data vectors.
        columns = ['Spec', 'Name', 'Temper', 'tmin', 'tmax', 'Basis', 'Et', 'Ec', 'G', 'nu', 'rho', 'u_sigma_t', 'y_sigma_t', 'y_sigma_c', 'units']
        flat_id = [value for value in self.id]
        flat_mech_props = [value for value in self.mech_props]
        flat_t = [value for value in self.t]
        flat_sigma = [value for value in self.sigma]
        data = flat_id[0:3] + flat_t + [flat_id[3]] + flat_mech_props + flat_sigma + [self.units]

        # Checking if the file is already created. If not, create it. Append values to file.
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_name = 'materials.csv'
        csv_file_path = os.path.join(script_dir, csv_file_name)

        if not os.path.isfile(csv_file_path):
            with open('materials.csv', 'w', newline='') as file:
                csv_writer = csv.writer(file)
                csv_writer.writerow(columns)
                csv_writer.writerow(data)
        else:
            with open('materials.csv', 'a', newline='') as file:
                csv_writer = csv.writer(file)
                csv_writer.writerow(data)


Al2024 = AddMaterial('AMS 4207', 'Al7475', 'T61', [0.188, 0.249], 'S', [10.0e3, 10.5e3], 3.8e3, 0.33, [72, 61, 65])
Al2024.append_to_csv()
