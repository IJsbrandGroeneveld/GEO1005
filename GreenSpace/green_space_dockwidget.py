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
        # initialize plugin directory
        self.plugin_path = os.path.dirname(__file__)


        # set up GUI operation signals
        self.iface.projectRead.connect(self.updateLayers)
        self.iface.newProjectCreated.connect(self.updateLayers)
        self.iface.legendInterface().itemRemoved.connect(self.updateLayers)
        self.iface.legendInterface().itemAdded.connect(self.updateLayers)
        self.selectLayerCombo.activated.connect(self.setSelectedLayer)
        self.selectAttributeCombo.activated.connect(self.setSelectedAttribute)
        self.selectFeatureCombo.activated.connect(self.setSelectedFeature)

        # select area boundary combobox
        self.selectLayerCombo.activated.connect(self.setSelectedLayer)
        self.selectAttributeCombo.activated.connect(self.setSelectedAttribute)
        self.selectFeatureCombo.activated.connect(self.setSelectedFeature)
        self.makeIntersectionButton.clicked.connect(self.calculateIntersection)
        self.startPushButton.clicked.connect(self.makeItGreen)
        # make buffer layer
        self.bufferPushButton.clicked.connect(self.calculateBuffer)
        self.clipButton.clicked.connect(self.newLayer)

        # add button icons
        self.startPushButton.setIcon(QtGui.QIcon(':icons/iconstart.png'))

        # add wanted green percentage
        self.percentagePushButton.clicked.connect(self.setPercentage)


        #reporting
        self.saveMapButton.clicked.connect(self.saveMap)
        self.saveMapPathButton.clicked.connect(self.selectFile)
        self.updateAttribute.connect(self.extractAttributeSummary)
        self.saveStatisticsButton.clicked.connect(self.saveTable)


        # initialisation
        self.updateLayers()

    def closeEvent(self, event):
        # disconnect interface signals
        try:
            self.iface.projectRead.disconnect(self.updateLayers)
            self.iface.newProjectCreated.disconnect(self.updateLayers)
            self.iface.legendInterface().itemRemoved.disconnect(self.updateLayers)
            self.iface.legendInterface().itemAdded.disconnect(self.updateLayers)
        except:
            pass

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
        for repo in report:
            self.reportList.addItems(repo)

    # get values from field
    def updateFeature(self):
        try:
            self.selectFeatureCombo.clear()
            layer = self.getSelectedLayer()
            if layer:
                attribute = self.getSelectedAttribute()
                features = uf.getFieldValues(layer, attribute, False, False)
                if features:
                    fea = []
                    for feature in features[0]:
                        fea.append(feature)
                    fea.sort()
                    self.selectFeatureCombo.addItems(fea)
                    self.setSelectedFeature()
                    # send list to the report list window
                    self.updateReport(fea)
        except:
            pass

    def setSelectedFeature(self):
        layer = self.getSelectedLayer()
        layer.removeSelection()
        att = str(self.selectAttributeCombo.currentText())
        feat = str(self.selectFeatureCombo.currentText())
        uf.selectFeaturesByExpression(layer, " %s = '%s' " % (att, feat))
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
        layer = uf.getLegendLayerByName(self.iface, "memory:clippedlayer")
        origins = layer.getFeatures()
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
            layer = QgsMapLayerRegistry.instance().mapLayersByName("Buffers")[0]
            toc = self.iface.legendInterface()
            groups = toc.groups()
            groupIndex = groups.index(u'output')
            toc.moveLayer(layer, groupIndex)

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
        layer = uf.getLegendLayerByName(self.iface, "green")

        # get the intersections between the two layers
        intersection = processing.runandload('qgis:intersection',layer,cutter,None)
        intersection_layer = uf.getLegendLayerByName(self.iface, "Intersection")
        # prepare results layer
        save_path = "%s/dissolve_results.shp" % QgsProject.instance().homePath()
        # dissolve grouping by origin id
        dissolve = processing.runandload('qgis:dissolve',intersection_layer,False,'id',save_path)
        dissolved_layer = uf.getLegendLayerByName(self.iface, "Dissolved")
        # close intersections intermediary layer
        """ QgsMapLayerRegistry.instance().removeMapLayers([intersection_layer.id()])"""

        # add an 'area' field and calculate
        # functiona can add more than one filed, therefore names and types are lists
        wanted_layer = uf.getLegendLayerByName(self.iface, "Buffers")
        dissolved_layer = uf.getLegendLayerByName(self.iface, "Dissolved")
        uf.addFields(dissolved_layer,["green_area"], [QtCore.QVariant.Double])
        uf.updateField(dissolved_layer, "green_area","$area")
        dissolved_layer.updateFields()
        save_path = "%s/dissolve_results.shp" % QgsProject.instance().homePath()

        shp = uf.getLegendLayerByName(self.iface, "Buffers")
        csv = uf.getLegendLayerByName(self.iface, "Dissolved")
        # Set properties for the join
        shpField='id'
        csvField='id'
        joinObject = QgsVectorJoinInfo()
        joinObject.joinLayerId = csv.id()
        joinObject.joinFieldName = csvField
        joinObject.targetFieldName = shpField
        joinObject.memoryCache = True
        shp.addJoin(joinObject)
        # add an 'total_area' field and calculate
        straal = float(self.bufferLineEdit.text())
        uf.addFields(wanted_layer, ["total_area"], [QtCore.QVariant.Double])
        uf.updateField(wanted_layer, "total_area"," 3.14159265359 * ((%d)^2)" % straal )
        # add an 'percentage_green' field and calculate
        uf.addFields(wanted_layer, ["green_perc"], [QtCore.QVariant.Double])
        uf.updateField(wanted_layer, "green_perc","(%s /%s)* 100" % ('Dissolved_green_area', 'total_area'))
        layer1 = QgsMapLayerRegistry.instance().mapLayersByName("Buffers")[0]
        layer2 = QgsMapLayerRegistry.instance().mapLayersByName("Intersection")[0]
        layer3 = QgsMapLayerRegistry.instance().mapLayersByName("Dissolved")[0]
        toc = self.iface.legendInterface()
        groups = toc.groups()
        groupIndex2 = groups.index(u'output')
        groupIndex = groups.index(u'working files')
        # move layer to output folder
        toc.moveLayer(layer1, groupIndex2)
        toc.moveLayer(layer2, groupIndex)
        toc.moveLayer(layer3, groupIndex)

    # make new layer from selected features
    def newLayer(self):
        layer = self.getSelectedLayer()
        att = str(self.selectAttributeCombo.currentText())
        feat = str(self.selectFeatureCombo.currentText())
        source_layer = uf.getLegendLayerByName(self.iface, "boundaries")
        new_layer = QgsVectorLayer('POLYGON?crs=EPSG:28992', "selected boundaries", "memory")
        provider = new_layer.dataProvider()
        features = [feat for feat in source_layer.selectedFeatures()]
        provider.addFeatures(features)
        #set layer style
        QgsMapLayerRegistry.instance().addMapLayer(new_layer)
        uri = os.path.normpath(self.plugin_path + "/styles/boundaries.qml")
        new_layer.loadNamedStyle(uri)
        #put layer in group
        toc = self.iface.legendInterface()
        groups = toc.groups()
        groupIndex = groups.index(u'working files')
        toc.moveLayer(new_layer, groupIndex)
        toc.setLayerVisible(source_layer, False)
        self.clipLayer()

    # clip layers function
    def clipLayer(self):
        inputlayer = uf.getLegendLayerByName(self.iface, "buildings")
        cliplayer = uf.getLegendLayerByName(self.iface, "selected boundaries")
        processing.runandload("qgis:clip", inputlayer, cliplayer, "memory:clippedlayer")
        layer = QgsMapLayerRegistry.instance().mapLayersByName("memory:clippedlayer")[0]
        toc = self.iface.legendInterface()
        groups = toc.groups()
        groupIndex = groups.index(u'working files')
        toc.setLayerVisible(layer, True)
        inputlayer2 = uf.getLegendLayerByName(self.iface, "green")
        cliplayer = uf.getLegendLayerByName(self.iface, "selected boundaries")
        processing.runandload("qgis:clip", inputlayer2, cliplayer, "memory:greenlayer")
        layer2 = QgsMapLayerRegistry.instance().mapLayersByName("memory:greenlayer")[0]
        toc = self.iface.legendInterface()
        groups = toc.groups()
        groupIndex = groups.index(u'working files')
        # move layer to output folder
        toc.moveLayer(layer, groupIndex)
        toc.moveLayer(layer2, groupIndex)
        toc.setLayerVisible(layer2, True)
        vLayer = uf.getLegendLayerByName(self.iface, "selected boundaries")
        canvas = self.iface.mapCanvas()
        extent = vLayer.extent()
        canvas.setExtent(extent)


    # set green percentage (add new field)
    def setPercentage(self):
        perc = int(self.percentageLineEdit.text())
        wanted_layer = uf.getLegendLayerByName(self.iface, "Buffers")
        uf.addFields(wanted_layer, ["wanted_perc"], [QtCore.QVariant.Double])
        uf.updateField(wanted_layer, "wanted_perc", "%d" % perc)

    def makeItGreen(self):
        layer1 = QgsMapLayerRegistry.instance().mapLayersByName("Buffers")[0]
        layer2 = QgsMapLayerRegistry.instance().mapLayersByName("Intersection")[0]
        layer3 = QgsMapLayerRegistry.instance().mapLayersByName("Dissolved")[0]
        toc = self.iface.legendInterface()
        toc.setLayerVisible(layer1, True)
        toc.setLayerVisible(layer2, False)
        toc.setLayerVisible(layer3, False)
        layer4 = QgsMapLayerRegistry.instance().mapLayersByName("memory:greenlayer")[0]
        layer5 = QgsMapLayerRegistry.instance().mapLayersByName("memory:clippedlayer")[0]
        toc = self.iface.legendInterface()
        toc.setLayerVisible(layer4, False)
        toc.setLayerVisible(layer5, False)
        # apply layer style
        # opens the qml stylefile and edits the rules
        file_path = os.path.normpath(self.plugin_path + "/styles/outputfiles.qml")
        file_path2 = os.path.normpath(self.plugin_path + "/styles/outputfiles2.qml")
        perc = int(self.percentageLineEdit.text())
        replacements = {
            """      <rule filter="green_perc >= 0 AND green_perc &lt; 10 " key="{9825544c-a679-41ac-af7c-10012f165b6f}" symbol="0" label="Onvoldoende 0.1 - 10.0 "/>""":
            """      <rule filter="green_perc >= 0.0 AND green_perc &lt;= """ + str(perc - (0.333 * perc)) + ' \"' + """ key="{9825544c-a679-41ac-af7c-10012f165b6f}" symbol="0" label="Onvoldoende "/>""",
            """      <rule filter="green_perc > 10.000000 AND green_perc &lt;= 20.000000" key="{cddc3e79-9186-4b56-92dc-f107f0f7bf0c}" symbol="1" label="Matig 10.0 - 20.0 "/>""":
            """      <rule filter="green_perc >= """ + str(perc-(0.333 * perc)) + """ AND green_perc &lt; """ + str(perc) + "\"" + """ key="{9825544c-a679-41ac-af7c-10012f165b6f}" symbol="1" label="Matig "/>""",
            """      <rule filter="green_perc > 20" key="{1e6b826e-d631-4fa1-8e6f-b23733e83b61}" symbol="2" label="Goed 10.0 - 20.0 "/>""":
            """      <rule filter="green_perc >= """ + str(perc) + '\"' + """ key="{1e6b826e-d631-4fa1-8e6f-b23733e83b61}" symbol="2" label="Goed "/>"""
             }
        lines = []
        with open(file_path) as infile:
            for line in infile:
                for src, target in replacements.iteritems():
                    line = line.replace(src, target)
                lines.append(line)
        with open(file_path2, 'w') as outfile:
            for line in lines:
                outfile.write(line)
        output_layer = uf.getLegendLayerByName(self.iface, "Buffers")
        output_layer.loadNamedStyle(file_path2)
        layertje = uf.getLegendLayerByName(self.iface, "brtachtergrondkaart")
        toc = self.iface.legendInterface()
        toc.setLayerVisible(layertje, True)
        toc = self.iface.legendInterface()
        groups = toc.groups()
        groupIndex12 = groups.index(u'working files')
        groupIndex13 = groups.index(u'input')
        toc.setGroupExpanded(groupIndex12, True)
        toc.setGroupExpanded(groupIndex13, True)






    # REPORT FUNCTIONS ---------------------------------------------------------------------------------------
    def updateNumberFeatures(self):
        try:
            layer = uf.getLegendLayerByName(self.iface, "Buffers")
            if layer:
                count = layer.featureCount()
                self.featureCounterEdit.setText(str(count))
        except:
            pass

    # selecting a file for saving
    def selectFile(self):
        try:
            last_dir = uf.getLastDir("SDSS")
            path = QtGui.QFileDialog.getSaveFileName(self, "Save map file", last_dir, "PNG (*.png)")
            if path.strip()!="":
                path = unicode(path)
                uf.setLastDir(path,"SDSS")
                self.saveMapPathEdit.setText(path)
        except:
            pass

    # saving the current screen
    def saveMap(self):
        try:
            filename = self.saveMapPathEdit.text()
            if filename != '':
                self.canvas.saveAsImage(filename,None,"PNG")
        except:
            pass

    def extractAttributeSummary(self, attribute):
        try:
            # get summary of the attribute
            layer = uf.getLegendLayerByName(self.iface, "Buffers")
            summary = []
            # only use the first attribute in the list
            for feature in layer.getFeatures():
                summary.append((feature.id(), feature.attribute(attribute)))
            # send this to the table
            self.clearTable()
            self.updateTable(summary)
        except:
            pass

    # report window functions
    def updateReport(self,report):
        self.reportList.clear()
        self.reportList.addItems(report)

    def insertReport(self,item):
        self.reportList.insertItem(0, item)

    def clearReport(self):
        self.reportList.clear()

    # table window functions
    def updateTable(self, values):
        try:
            # takes a list of label / value pairs, can be tuples or lists. not dictionaries to control order
            self.statisticsTable.setColumnCount(2)
            self.statisticsTable.setHorizontalHeaderLabels(["Item","Value"])
            self.statisticsTable.setRowCount(len(values))
            for i, item in enumerate(values):
                # i is the table row, items mus tbe added as QTableWidgetItems
                self.statisticsTable.setItem(i,0,QtGui.QTableWidgetItem(str(item[0])))
                self.statisticsTable.setItem(i,1,QtGui.QTableWidgetItem(str(item[1])))
            self.statisticsTable.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
            self.statisticsTable.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
            self.statisticsTable.resizeRowsToContents()
        except:
            pass

    def clearTable(self):
        self.statisticsTable.clear()

    def saveTable(self):
        try:
            path = QtGui.QFileDialog.getSaveFileName(self, 'Save File', '', 'CSV(*.csv)')
            if path:
                with open(unicode(path), 'wb') as stream:
                    # open csv file for writing
                    writer = csv.writer(stream)
                    # write header
                    header = []
                    for column in range(self.statisticsTable.columnCount()):
                        item = self.statisticsTable.horizontalHeaderItem(column)
                        header.append(unicode(item.text()).encode('utf8'))
                    writer.writerow(header)
                    # write data
                    for row in range(self.statisticsTable.rowCount()):
                        rowdata = []
                        for column in range(self.statisticsTable.columnCount()):
                            item = self.statisticsTable.item(row, column)
                            if item is not None:
                                rowdata.append(
                                    unicode(item.text()).encode('utf8'))
                            else:
                                rowdata.append('')
                        writer.writerow(rowdata)
        except:
            pass