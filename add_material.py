import csv
import numpy as np


class AddMaterial:
    """
    Adds a new material to the .csv material input file. Standardized to accept metals only.
    Suggested reference: MIL-HDBK-5J.

    Attributes
    ----------
    :name :
    :coords :

    Methods
    -------
    :create_metal :
    :append_to_csv :

    """

    def __init__(self, name: str, rho, E_vector, G_vector, nu, sigma_vector):
        self.name = name
        self.rho = rho
        self.E_vector = E_vector
        self.G_vector = G_vector
        self.nu = nu
        self.sigma_vector = sigma_vector

    def append_to_csv(self):
        """
        Appends the created material to the .csv input file.
        """

        column_names = ['Name', 'Et', 'Ec', 'G', 'nu', 'ult_sigma_t', 'yield_sigma_t', 'yield_sigma_c']

        # Separating variables.
        E_t = self.E_vector[0]
        E_c = self.E_vector[1]
        G = self.G_vector

        # Appending to .csv.



        with open('material_list.csv', 'w') as file:
            csvreader = csv.reader(file)

