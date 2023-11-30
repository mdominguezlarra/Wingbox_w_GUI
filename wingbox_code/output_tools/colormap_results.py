from random import random
from parapy.core import *
from parapy.geom import *
from parapy.lib.fem.future.mesh.visualization import DeformedGrid


class Colormap(GeomBase):

    mesh = Input()
    dictn = Input()
    magnification_factor = Input()

    @Attribute
    def get_vectors(self):

        disp_dicts = []
        for key in self.dictn.keys():
            lst = self.dictn[key]
            node_id_to_vector = dict()
            for node in lst:
                node_id_to_vector[node[0]] = Vector(float(node[1]), float(node[2]), float(node[3]))
            disp_dicts.append(node_id_to_vector)

        return disp_dicts

    @Part
    def displacements(self):
        return DeformedGrid(quantify=len(self.get_vectors),
                            SMESH_Mesh=self.mesh.SMESH_Mesh,
                            vectors=self.get_vectors[child.index],
                            magnify=self.magnification_factor,
                            colors=((0, 0, 255), (255, 0, 0)))


if __name__ == '__main__':
    from parapy.gui import display
    display(Colormap)

