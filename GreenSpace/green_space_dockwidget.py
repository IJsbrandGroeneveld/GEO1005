# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GreenSpaceDockWidget
                                 A QGIS plugin
 This tool can be used to support green area planning in the built environment.
                             -------------------
        begin                : 2015-12-03
        git sha              : $Format:%H$
        copyright            : (C) 2015 by TU Delft
        email                :
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# module imports
import os
import os.path
import processing
from qgis.core import *

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal

# import the utility functions file
from . import utility_functions as uf

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'green_space_dockwidget_base.ui'))


class GreenSpaceDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(GreenSpaceDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # define globals
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        # set up GUI operation signals
        # data
        self.selectLayerCombo.activated.connect(self.setSelectedLayer)

        # initialisation
        self.updateLayers()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def updateLayers(self):
        layers = uf.getLegendLayers(self.iface, 'all', 'all')
        self.selectLayerCombo.clear()
        if layers:
            layer_names = uf.getLayersListNames(layers)
            self.selectLayerCombo.addItems(layer_names)
            self.setSelectedLayer()
        #else:
         #   self.selectAttributeCombo.clear()

    def setSelectedLayer(self):
        layer_name = self.selectLayerCombo.currentText()
        layer = uf.getLegendLayerByName(self.iface,layer_name)
        #self.updateAttributes(layer)

    def getSelectedLayer(self):
        layer_name = self.selectLayerCombo.currentText()
        layer = uf.getLegendLayerByName(self.iface,layer_name)
        return layer