from vispy.scene.visuals import Markers
from vispy.scene.visuals import Line
from vispy.scene.visuals import Text
from vispy.scene.visuals import Compound

from napari._vispy.vispy_base_layer import VispyBaseLayer

import numpy as np

from ._track_shader import TrackShader

class VispyTracksLayer(VispyBaseLayer):
    """ VispyTracksLayer

    Custom napari Track layer for visualizing tracks.


    TODO(arl): should we always provide 3D data to the subvisual, and then
        adjust the values for the n-th dimension when changing the displayed
        dimension? or... rebuild the whole visual when changing?

    """
    def __init__(self, layer):
        # node = Line()
        node = Compound([Line(), Text(method='gpu')])
        super().__init__(layer, node)

        self.layer.events.edge_width.connect(self._on_data_change)
        self.layer.events.tail_length.connect(self._on_data_change)
        self.layer.events.display_id.connect(self._on_data_change)
        self.layer.events.color_by.connect(self._on_color_by)

        # if the dimensions change, we need to update the data
        self.layer.dims.events.ndisplay.connect(self._on_dimensions_change)

        # get the data
        self._positions = self.layer._view_data()

        # build and attach the shader to the track
        self.shader = TrackShader(current_time=0,
                                  tail_length=self.layer.tail_length,
                                  vertex_time=self.layer.vertex_times)

        node._subvisuals[0].attach(self.shader)

        # now set the data for the track lines
        self.node._subvisuals[0].set_data(pos=self._positions,
                                          color=self.layer.vertex_colors,
                                          connect=self.layer.vertex_connex)

        self.node._subvisuals[1].color = 'white'
        self.node._subvisuals[1].font_size = 8

        self._reset_base()
        self._on_data_change()


    def _on_data_change(self, event=None):
        """ update the display

        NOTE(arl): this gets called by the VispyBaseLayer

        """
        # update the shader
        self.shader.current_time = self.layer.current_frame
        self.shader.tail_length = self.layer.tail_length
        self.node._subvisuals[0].set_data(width=self.layer.edge_width)

        # update the track IDs
        self.node._subvisuals[1].visible = self.layer.display_id

        if self.node._subvisuals[1].visible:
            text, pos = zip(*self.layer.track_labels)
            self.node._subvisuals[1].text = text
            self.node._subvisuals[1].pos = pos

        self.node.update()
        # Call to update order of translation values with new dims:
        self._on_scale_change()
        self._on_translate_change()


    def _on_dimensions_change(self, event=None):
        """ if we change dimensions, change the display of the tracks.

        Rationale:
            (2d+t) tracks in 2D should be a projection of t
            (2d+t) tracks in 3D should be the complete trees
            (3d+t) tracks in 3D should be a projection of t, or the complete trees?
        """
        print(self.layer.dims.displayed)
        print(self.layer.dims.not_displayed)
        # self.layer._view_data()
        #
        # self.node._subvisuals[0].set_data(pos=self.layer.data)
        #
        # self.node.update()
        # # Call to update order of translation values with new dims:
        # self._on_scale_change()
        # self._on_translate_change()


    def _on_color_by(self, event=None):
        """ change the coloring only """
        self.node._subvisuals[0].set_data(color=self.layer.vertex_colors)
        self.node.update()
        # Call to update order of translation values with new dims:
        self._on_scale_change()
        self._on_translate_change()
