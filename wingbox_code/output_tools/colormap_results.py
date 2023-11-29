from random import random
from parapy.core import *
from parapy.geom import *
from parapy.lib.fem.future.mesh.visualization import DeformedGrid


class Colormap(GeomBase):

    mesh = Input()
    magnification_factor = Input()

    @Attribute
    def get_vectors(self):

        node_id_to_vector = dict()

        for node in self.mesh.grid.nodes:
            node_id_to_vector[node.mesh_id] = Vector(random(), random(), random())

        return node_id_to_vector, node_id_to_vector, node_id_to_vector

    @Part
    def displacements(self):
        return DeformedGrid(SMESH_Mesh=self.mesh.SMESH_Mesh,
                            vectors=self.get_vectors[0],
                            magnify=self.magnification_factor,
                            colors=((255, 0, 0), (0, 0, 255)))

    @Part
    def stresses(self):
        return DeformedGrid(SMESH_Mesh=self.mesh.SMESH_Mesh,
                            vectors=self.get_vectors[1],
                            magnify=self.magnification_factor,
                            colors=((255, 0, 0), (0, 0, 255)))

    @Part
    def strains(self):
        return DeformedGrid(SMESH_Mesh=self.mesh.SMESH_Mesh,
                            vectors=self.get_vectors[2],
                            magnify=self.magnification_factor,
                            colors=((255, 0, 0), (0, 0, 255)))


if __name__ == '__main__':
    from parapy.gui import display
    display(Colormap)

