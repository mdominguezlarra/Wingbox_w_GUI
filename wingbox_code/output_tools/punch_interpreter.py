import os

def read_punch(punch_path):
    """ Read the punch file and appends results to homonymous dictionaries. """
    type_marker = 0
    type_vector = []
    subcase_vector = []
    content_marker = 0
    content_vector = []
    content_aux = []

    with open(punch_path, 'r') as file:
        for line_num, line in enumerate(file, 1):

            # Treating header and appending content vector if a new output section has begun.
            if '$' in line:
                if content_marker != 0:
                    content_vector.append(content_aux)
                    content_aux = []
                    content_marker = 0

                # Appending to which analysis the set of results refer to.
                if type_marker != 0:
                    if line.split()[0][1] == 'D':
                        type = line.split()[0][1:]
                    else:
                        type = line.split()[1][0:]
                    type_marker -= 1
                    type_vector.append(type)

                if line.startswith('$LABEL'):
                    type_marker += 1

                # Appending to which subcase the set of results refer to.
                if line.startswith('$SUBCASE ID'):
                    subcase, marker = (int(line.split()[3]), int(line.split()[4]) + 1)
                    subcase_vector.append(subcase)

                continue

            # Getting the content vectors.
            if line.startswith('-CONT-'):
                node_values = [str(value) for value in line.split()[1:-1]]
                content_aux[-1].extend(node_values)
                continue

            if len(type_vector) <= 3:
                node_values = [int(line.split()[0])]
                node_values.extend([str(value) for value in line.split()[2:5]])
            else:
                node_values = [int(value) if idx == 0 else str(value) for idx, value in enumerate(line.split()[0:-1])]

            content_aux.append(node_values)
            content_marker = 1

    # Appending the last vector.
    content_vector.append(content_aux)

    # Appending results to the respective dictionaries.
    disp_dict = {subcase_vector[idx]: content_vector[idx] for idx, typ in enumerate(type_vector) if
                 typ == 'DISPLACEMENTS'}
    stress_dict = {subcase_vector[idx]: content_vector[idx] for idx, typ in enumerate(type_vector) if typ == 'STRESSES'}
    strain_dict = {subcase_vector[idx]: content_vector[idx] for idx, typ in enumerate(type_vector) if typ == 'STRAINS'}

    return disp_dict, stress_dict, strain_dict


def displacements_parsing(disp_dict, mesh_nodes):
    """ Parses the displacement results from the punch file. """

    for key in disp_dict.keys():
        dictn = disp_dict[key]

        write_path = os.path.join(os.getcwd(), r'wingbox_code\output_data\categorized_outputs\displacements',
                                               r'displacements_SUBCASE' + str(key) + '.txt')
        with open(write_path, 'w') as file:

            # Header.
            output_header = ""
            header_content = ['node', 'x', 'y', 'z', 'ux', 'uy', 'uz', 'rx', 'ry', 'rz']
            for j in range(len(header_content)):
                diff_value = 16 - len(header_content[j]) if j != 0 else 11 - len(header_content[j])
                output_header += header_content[j] + " " * diff_value
            file.write(output_header + '\n')

            # Writing each line.
            for j in range(len(dictn)):

                # Getting node coordinates.
                coords = [mesh_nodes[j][0], mesh_nodes[j][1], mesh_nodes[j][2]]
                coords_str = [f'{number:.6e}'.upper() for number in coords]

                # Writing node identification label.
                output_line = ""
                output_line += str(dictn[j][0]) + (11 - len(str(dictn[j][0]))) * " "

                # Writing node coordinates.
                add = 0
                for coord in coords_str:
                    if coord[0] == '-':
                        output_line = output_line[:-1]
                        add = 1
                    output_line += coord + (16 - len(coord) + add) * " "
                    add = 0

                add = 0
                # Writing displacement and rotation values.
                for idx, value in enumerate(dictn[j]):
                    if idx != 0:
                        if value[0] == '-':
                            output_line = output_line[:-1]
                            add = 1
                        output_line += value + (16 - len(value) + add) * " "
                        add = 0

                file.write(output_line + '\n')


def stress_strain_parsing(dict, selector):
    """ Parses the stress results from the punch file. """

    if selector == 'stresses':
        path_str = 'stresses'
    elif selector == 'strains':
        path_str = 'strains'

    for key in dict.keys():
        dictn = dict[key]

        path_str_1 = r'wingbox_code\output_data\categorized_outputs\\' + path_str
        path_str_2 = path_str + '_SUBCASE'
        write_path = os.path.join(os.getcwd(), path_str_1, path_str_2 + str(key) + '.txt')
        with open(write_path, 'w') as file:

            # Header.
            output_header = ""
            header_content = ['element', 'fiber_dist', 'sigma_XX', 'sigma_YY', 'tau_XY', 'skew_angle', 'princ_major',
                              'princ_minor', 'von_mises']
            for j in range(len(header_content)):
                diff_value = 16 - len(header_content[j]) if j != 0 else 11 - len(header_content[j])
                output_header += header_content[j] + " " * diff_value
            file.write(output_header + '\n')

            # Writing each line.
            for j in range(len(dictn)):

                lst_1 = dictn[j][1:9]
                lst_2 = dictn[j][9: ]

                output_line_1, output_line_2 = "", ""

                # Writing node identification label.
                output_line_1 += str(dictn[j][0]) + (11 - len(str(dictn[j][0]))) * " "
                output_line_2 += 11 * " "

                # First line of an element stress.
                add = 0
                for idx, value in enumerate(lst_1):
                    if value[0] == '-':
                        output_line_1 = output_line_1[:-1]
                        add = 1
                    output_line_1 += value + (16 - len(value) + add) * " "
                    add = 0

                # Second line of an element stress.
                add = 0
                for idx, value in enumerate(lst_2):
                    if value[0] == '-':
                        output_line_2 = output_line_2[:-1]
                        add = 1
                    output_line_2 += value + (16 - len(value) + add) * " "
                    add = 0

                file.write(output_line_1 + '\n')
                file.write(output_line_2 + '\n')


def punch_interpreter(mesh_nodes):
    """ Interprets punch file and save formatted results to 'output_data' folders. """

    # Punch file reading.
    punch_path = os.path.join(os.getcwd(), r'wingbox_code\output_data\raw_NASTRAN_output\wingbox_bulkdata.pch')
    disp_dict, stress_dict, strain_dict = read_punch(punch_path)

    # Results parsing.
    displacements_parsing(disp_dict, mesh_nodes)
    stress_strain_parsing(stress_dict, 'stresses')
    stress_strain_parsing(stress_dict, 'strains')