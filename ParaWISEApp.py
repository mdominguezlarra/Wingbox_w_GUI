from parapy.webgui.core import Component, NodeType, get_assets_dir, get_asset_url, State
from parapy.webgui import layout
from parapy.webgui.app_bar import AppBar
from parapy.webgui import mui
from parapy.webgui import viewer
from parapy.exchange import STEPWriter
from AA_Initialization import WING
import numpy as np
# fppkbe2023
# cyj8kS8VVN60
import os
from parapy.webgui.core.actions import download_file


class App(Component):

    def render(self) -> NodeType:
        return layout.Split(orientation='vertical',
                            weights=[0, 1],
                            style={'backgroundColor': 'white'},
                            height='100%')[
            AppBar(title="ParaWISE", showIAMButton=False, showUserInfo=False,
                   children=layout.Box(orientation='horizontal',
                                       h_align='right',
                                       v_align='center',
                                       height='100%'
                                       )[
                            mui.Button(variant='contained',
                                       onClick=self.geom_view,
                                       )[
                                "GEOM"
                            ],
                            mui.Button(variant='contained',
                                       onClick=self.avl_view
                                       )[
                                "AERO"
                            ],
                            mui.Button(variant='contained',
                                       onClick=self.struc_view)[
                                "STRUC"
                            ],
                            mui.Button(variant='contained',
                                       onClick=self.nastran_view
                                       )[
                                "NASTRAN"
                            ],
                    ]),
            layout.Split(height='100%',
                         weights=[0, 0, 1])[
                InputsPanel,
                mui.Divider(orientation='vertical'),
                viewer.Viewer(objects=self.DISPLAY)
            ]
        ]

    # @property
    # def DISPLAY(self):
    #     return [WING.wing_geom.right_wing]

    DISPLAY: list = State([WING.wing_geom.right_wing, WING.wing_geom.left_wing])

    # @property
    # def DISPLAY(self):
    #     return self._DISPLAY
    #
    # @State
    # @DISPLAY.setter
    # def DISPLAY(self, val):
    #     self.DISPLAY = val

    def geom_view(self, evt):
        self.DISPLAY = [WING.wing_geom.right_wing]
        return

    def avl_view(self, evt):
        self.DISPLAY = [[WING.wing_geom.right_wing, WING.wing_geom.left_wing]]
        return

    def struc_view(self, evt):
        self.DISPLAY = [WING.wingbox.spars, WING.wingbox.ribs, WING.wingbox.stringers]
        return

    def nastran_view(self, evt):
        self.DISPLAY = []
        return



class InputsPanel(Component):
    def render(self) -> NodeType:
        return layout.Box(orientation='vertical',
                          gap='1em',
                          style={'padding': '1em'})['eyo']




if __name__ == "__main__":
    from parapy.webgui.core import display
    display(App, reload=True)