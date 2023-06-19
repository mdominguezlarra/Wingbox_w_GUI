def generate_warning(warning_header, msg):
    """
    This function generates the warning dialog box
    :param warning_header: The text to be shown on the dialog box header
    :param msg: the message to be shown in dialog box
    :return: None as it is GUI operation
    """
    from tkinter import Tk, messagebox

    # initialization
    window = Tk()
    window.withdraw()

    # generates message box
    messagebox.showwarning(warning_header, msg)

    # kills the gui
    window.deiconify()
    window.destroy()
    window.quit()


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
        return False, msg

    return True, None

def material_validation():
    """
    Performs validation of the material name with the data from the datasheet.
    :return: list of valid names and thicknesses
    """
    import csv

    # List initialization
    names = []
    temper = []
    basis = []
    partial_name = []
    thicknesses = []

    # Finding the correct mechanical properties.
    path = 'wingbox_code/input_data/materials.csv'
    with open(path, 'r', newline='') as file:
        mat_file = csv.reader(file)

        for idx, row in enumerate(mat_file):
            if idx != 0:
                names.append(row[1])
                temper.append(row[2])
                basis.append(row[5])

                row_str = row[1] + '-' + row[2] + '-' + row[5]
                partial_name.append(row_str)

                t_lims = [float(row[3]), float(row[4])]
                thicknesses.append(t_lims)

    return names, temper, basis, partial_name, thicknesses

