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

from PyQt4 import QtGui, uic, QtCore
from PyQt4.QtCore import pyqtSignal

# import the utility functions file
from . import utility_functions as uf

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'green_space_dockwidget_base.ui'))


class GreenSpaceDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = QtCore.pyqtSignal()
    #custom signals
    updateAttribute = QtCore.pyqtSignal(str)

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

        # select area boundary combobox
        self.selectLayerCombo.activated.connect(self.setSelectedLayer)
        self.selectAttributeCombo.activated.connect(self.setSelectedAttribute)
        self.selectFeatureCombo.activated.connect(self.setSelectedFeature)
        self.makeIntersectionButton.clicked.connect(self.calculateIntersection)

        # make buffer layer
        self.bufferPushButton.clicked.connect(self.calculateBuffer)
        self.clipButton.clicked.connect(self.clipLayer)

        # add button icons
        self.startPushButton.setIcon(QtGui.QIcon(':iconsjes/iconStart.png'))

        # initialisation
        self.updateLayers()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    # layer and attribute functions
    def updateLayers(self):
        layers = uf.getLegendLayers(self.iface, 'all', 'all')
        self.selectLayerCombo.clear()
        if layers:
            layer_names = uf.getLayersListNames(layers)
            self.selectLayerCombo.addItems(layer_names)
            self.setSelectedLayer()
        else:
            self.selectAttributeCombo.clear()


    def setSelectedLayer(self):
        layer_name = self.selectLayerCombo.currentText()
        layer = uf.getLegendLayerByName(self.iface,layer_name)
        self.updateAttributes(layer)

    def getSelectedLayer(self):
        layer_name = self.selectLayerCombo.currentText()
        layer = uf.getLegendLayerByName(self.iface,layer_name)
        return layer

    def updateAttributes(self, layer):
        self.selectAttributeCombo.clear()
        if layer:
            fields = uf.getFieldNames(layer)
            if fields:
                self.selectAttributeCombo.addItems(fields)
                self.setSelectedAttribute()
                # send list to the report list window
                self.updateReport(fields)

    def setSelectedAttribute(self):
        field_name = self.selectAttributeCombo.currentText()
        self.updateFeature()
        self.updateAttribute.emit(field_name)

    def getSelectedAttribute(self):
        field_name = self.selectAttributeCombo.currentText()
        return field_name

    def updateReport(self,report):
        self.reportList.clear()
        self.reportList.addItems(report)

    # get values from field
    def updateFeature(self):
        self.selectFeatureCombo.clear()
        layer = self.getSelectedLayer()
        if layer:
            attribute = self.getSelectedAttribute()
            features = uf.getFieldValues(layer, attribute, True, False)
            if features:
                self.selectFeatureCombo.addItems(features)
                self.setSelectedFeatures()
                # send list to the report list window
                self.updateReport(features)


    def setSelectedFeature(self):
        feature = self.selectFeatureCombo.currentText()
        self.updateAttribute.emit(feature)

    def getSelectedFeature(self):
        feature_name = self.selectFeatureCombo.currentText()
        return feature_name

    # buffer functions
    def getBufferCutoff(self):
        cutoff = self.bufferLineEdit.text()
        if uf.isNumeric(cutoff):
            return uf.convertNumeric(cutoff)
        else:
            return 0

    def calculateBuffer(self):
        origins = self.getSelectedLayer().selectedFeatures()
        layer = self.getSelectedLayer()
        if origins > 0:
            cutoff_distance = self.getBufferCutoff()
            buffers = {}
            for point in origins:
                geom = point.geometry()
                buffers[point.id()] = geom.buffer(cutoff_distance,11).asPolygon()
            # store the buffer results in temporary layer called "Buffers"
            buffer_layer = uf.getLegendLayerByName(self.iface, "Buffers")
            # create one if it doesn't exist
            if not buffer_layer:
                attribs = ['id', 'distance']
                types = [QtCore.QVariant.String, QtCore.QVariant.Double]
                buffer_layer = uf.createTempLayer('Buffers','POLYGON',layer.crs().postgisSrid(), attribs, types)
                uf.loadTempLayer(buffer_layer)
            # insert buffer polygons
            geoms = []
            values = []
            for buffer in buffers.iteritems():
                # each buffer has an id and a geometry
                geoms.append(buffer[1])
                # in the case of values, it expects a list of multiple values in each item - list of lists
                values.append([buffer[0],cutoff_distance])
            uf.insertTempFeatures(buffer_layer, geoms, values)
            self.refreshCanvas(buffer_layer)

    def refreshCanvas(self, layer):
        if self.canvas.isCachingEnabled():
            layer.setCacheImage(None)
        else:
            self.canvas.refresh()

    # intersection function
    def calculateIntersection(self):
        # use the buffer to cut from another layer
        cutter = uf.getLegendLayerByName(self.iface, "Buffers")
        # use the selected layer for cutting
        layer = uf.getLegendLayerByName(self.iface, "Terrain clipped green land cover")
        if cutter.featureCount() > 0:
            # get the intersections between the two layers
            intersection = processing.runandload('qgis:intersection',layer,cutter,None)
            intersection_layer = uf.getLegendLayerByName(self.iface, "Intersection")
            # prepare results layer
            save_path = "%s/dissolve_results.shp" % QgsProject.instance().homePath()
            # dissolve grouping by origin id
            dissolve = processing.runandload('qgis:dissolve',intersection_layer,False,'id',save_path)
            dissolved_layer = uf.getLegendLayerByName(self.iface, "Dissolved")
            # close intersections intermediary layer
            QgsMapLayerRegistry.instance().removeMapLayers([intersection_layer.id()])

            # add an 'area' field and calculate
            # functiona can add more than one filed, therefore names and types are lists
            uf.addFields(dissolved_layer, ["area"], [QtCore.QVariant.Double])
            uf.updateField(dissolved_layer, "area","$area")
            # add an 'total_area' field and calculate
            uf.addFields(dissolved_layer, ["total_area"], [QtCore.QVariant.Double])
            uf.updateField(dissolved_layer, "total_area","$area")
            # add an 'percentage_green' field and calculate
            uf.addFields(dissolved_layer, ["perc_green"], [QtCore.QVariant.Double])
            uf.updateField(dissolved_layer, "perc_green","$area")

    # clip layers function
    def clipLayer(self):
        inputlayer = uf.getLegendLayerByName(self.iface, "Buffer 300")
        cliplayer = uf.getLegendLayerByName(self.iface, "Terrain clipped green land cover")
        processing.runalg("qgis:clip",inputlayer, cliplayer, "clipped_layer.shp")
        pass

