import abc
from typing import List, Optional

import napari
from qtpy.QtWidgets import QWidget

from ..graph import TreeNode, build_subgraph
from ..tree import Annotation, Edge, layout_tree

GUI_MAXIMUM_WIDTH = 600

__all__ = ["TreePlotterBase", "TreePlotterQWidgetBase"]


class TreePlotterBase(abc.ABC):
    """
    Base class for a `napari.layers.Tracks` plotter.

    This class is designed to handle the translation from a `napari.layers.Tracks`
    layer to visual objects that can be plotted (e.g. lines, text). As such its
    only state is the ``_tracks`` attribute.

    This is not designed to actually render the plotting objects objects.
    Sub-classes should do that by impelmenting the abstract methods defined below.

    Attributes
    ----------
    edges : List[Edge]
    annotations : List[Annotation]
    """

    @property
    def tracks(self) -> napari.layers.Tracks:
        """
        The napari tracks layer associated with this plotter.
        """
        if not self.has_tracks:
            raise AttributeError("No tracks set on this plotter.")
        return self._tracks

    @tracks.setter
    def tracks(self, track_layer: napari.layers.Tracks) -> None:
        self._tracks = track_layer

    @property
    def has_tracks(self) -> bool:
        return hasattr(self, "_tracks")

    def draw_tree(self, track_id: int) -> None:
        """
        Plot the tree containing ``track_id``.
        """
        self.clear()
        root, subgraph_nodes = build_subgraph(self.tracks, track_id)
        self.draw_from_nodes(subgraph_nodes, track_id)

    def draw_from_nodes(
        self, tree_nodes: List[TreeNode], track_id: Optional[int] = None
    ):
        self.edges, self.annotations = layout_tree(tree_nodes)

        if self.has_tracks:
            self.update_edge_colors(update_live=False)

        for e in self.edges:
            self.add_branch(e)

        # labels
        for a in self.annotations:
            # change the alpha value according to whether this is the selected
            # cell or another part of the tree
            a.color[3] = 1 if a.label == str(track_id) else 0.25
            self.add_annotation(a)

    def update_edge_colors(self, update_live: bool = True) -> None:
        """
        Update tree edge colours from the track properties.

        Parameters
        ----------
        update_live : bool
            If `True`, also call `update_colors()` on the plotting backend
            to update the colors in a live plot.
        """
        for e in self.edges:
            if e.id is not None:
                e.color = self.tracks.track_colors[
                    self.tracks.properties["track_id"] == e.id
                ]

        if update_live:
            self.update_colors()

    @abc.abstractmethod
    def update_colors(self) -> None:
        """
        Use the colors stored in self.edges to update the colors in a live
        plot.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def clear(self) -> None:
        """
        Clear the plotting canvas. Called to remove the previous tree when
        a new tree is drawn.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def add_branch(self, e: Edge) -> None:
        """
        Add a single branch to the tree.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def add_annotation(self, a: Annotation) -> None:
        """
        Add a single label to the tree.
        """
        raise NotImplementedError()


class TreePlotterQWidgetBase(TreePlotterBase):
    """
    Base class for a tree plotter that provides a QWidget
    (e.g. for embedding in a napari plugin).
    """

    @abc.abstractmethod
    def get_qwidget(self) -> QWidget:
        """
        Return the native QWidget for embedding.
        """
        raise NotImplementedError()
