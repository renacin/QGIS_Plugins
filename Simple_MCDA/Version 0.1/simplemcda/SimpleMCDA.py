# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SimpleMCDA
                                 A QGIS plugin
 This plugin will allow users to implement a simple single synthesis MCDA.
 Put simply this plugin will create a composite variable through the use of
 weights, and raw variables.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2018-06-17
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Ryerson University
        email                : renacin.matadeen@ryerson.ca
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

from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QFileDialog

# From qgis.core import everything to give a greater level of functionality
from qgis.core import *
from qgis.utils import *
from qgis.gui import *

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .SimpleMCDA_dialog import SimpleMCDADialog
import os
import os.path

# ---------------------------------------------------------------------------


class SimpleMCDA:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SimpleMCDA_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = SimpleMCDADialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Simple MCDA')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'SimpleMCDA')
        self.toolbar.setObjectName(u'SimpleMCDA')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SimpleMCDA', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    # -----------------------------------------------------------------------
    # This Is Where The GUI Is Set

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/SimpleMCDA/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Simple MCDA'),
            callback=self.run,
            parent=self.iface.mainWindow())

        self.loadVectors()

    # ---------------------------------------------------------------------------
    # This Is Where Most Of The Operational Functions Are Set

    def loadVectors(self):
        """Creates A Drop-down with vector files currently in the legend"""
        # Clear Anything In The Drop-down Just In Case
        self.dlg.cb_inVector.clear()
        self.dlg.le_inVariables.clear()
        self.dlg.le_inWeights.clear()

        layers = [layer for layer in QgsProject.instance().mapLayers().values()]
        # Create a New Layer To Store The Names Of Vector Layers
        vector_layers = []
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer:
                vector_layers.append(layer.name())
        # Display The List In The cb.inVector object
        self.dlg.cb_inVector.addItems(vector_layers)

    def getVectorLayer(self):
        """This will get the vector layer data"""
        # Get The Name Of The Layer Then Loop Through The Layers In The TOC Looking For A Match
        layer = None
        layername = self.dlg.cb_inVector.currentText()
        for lyr in QgsProject.instance().mapLayers().values():
            if lyr.name() == layername:
                layer = lyr
                break

        # Once A Match Has Been Found Break The Loop & Return
        return layer

    def setVariables(self):
        """Get and set all variables from UI"""

        # Remember There Are Three Main Values From The UI
        self.inVector = self.getVectorLayer()
        self.inVariables = self.dlg.le_inVariables.text()
        self.inWeights = self.dlg.le_inWeights.text()

    def check_match(self):
        """Checks To See If All Inputs Are Correct"""

        # Insure That The Focus Fields Match The Fields Inside The Vector
        # And Insure The Number Of Focus Variables Matches The Number Of Weights

        # Get All The Fields From The Vector Layer
        fields = self.inVector.fields()
        field_names = []
        for field in fields:
            field_names.append(str(field.name()))

        # Clean Variables Input
        raw_user_fields = self.dlg.le_inVariables.text()
        user_fields = raw_user_fields.replace(" ", "")
        user_fields = user_fields.split(",")

        # Check If Variables In Vector
        for user_field in user_fields:
            if user_field in field_names:
                pass
            else:
                iface.messageBar().pushMessage("Input Error!", "Variable Not In Vector", duration=4)
                raise IOError

        # Clean Weights Input
        raw_user_weights = self.dlg.le_inWeights.text()
        user_weights = raw_user_weights.replace(" ", "")
        user_weights = user_weights.split(",")

        # Check To See If Number Of Weights Matched The Number Of Focus Fields
        if len(user_weights) == len(user_fields):
            pass
        else:
            iface.messageBar().pushMessage("Input Error!", "Number Of Weights != Number Of Variables", duration=4)
            raise IOError

        # Check To See If Number Of Weights Adds Up To 1
        total_weight = float(0)
        for weight in user_weights:
            total_weight = total_weight + float(weight)

        if total_weight <= float(1):
            pass
        else:
            iface.messageBar().pushMessage("Input Error!", "Weights Do Not Add Up To 1", duration=4)
            raise IOError

    def simple_mcda(self):
        """Create A New Vector File Containing The Calculated Composite Field"""

        # Get Path & Additional Info Of Vector Layer
        self.inVector = self.getVectorLayer()
        filepath = self.inVector.dataProvider().dataSourceUri()
        filepath = filepath.split("|")
        file_path = filepath[0]
        filepath = filepath[0]

        filename = filepath.split("/")
        filename = filename[len(filename) - 1]

        folderpath = filepath.replace(filename, "")
        name = filename.replace(".shp", "")

        # Get Specific Fields
        raw_user_fields = self.dlg.le_inVariables.text()
        user_fields = raw_user_fields.replace(" ", "")
        user_fields = user_fields.split(",")

        # Get Specific Weights
        raw_user_weights = self.dlg.le_inWeights.text()
        user_weights = raw_user_weights.replace(" ", "")
        user_weights = user_weights.split(",")

        # Get Vector Fields
        fields = self.inVector.fields()
        field_names = []
        for field in fields:
            field_names.append(str(field.name()))

        # Get Index Place Of Each Focus Feature, With Respect To The Vector File
        ff_index = []
        for user_field in user_fields:
            ff_index.append(field_names.index(user_field))

        # Create An Appropriate Number Of Lists
        for user_def_field in ff_index:
            exec("field_index_" + str(user_def_field) + " = []")

        # Create An Equivalent Number Of Lists Each For Specific Features
        for feature in self.inVector.getFeatures():
            temp_list = []
            for attr in feature:
                temp_list.append(attr)

            for user_def_field in ff_index:
                exec("field_index_" + str(user_def_field) + ".append(temp_list[int(user_def_field)])")

        # Create A Composite List To Store Comp Values
        composite_list = []

        # Get Values For A Specific Row, From Each List
        exec("list_dim = len(field_index_1)")
        for x in range(int(self.inVector.featureCount())):

            # Weight Variables Appropriately
            counter_x = 0

            global composite_value
            composite_value = float(0)

            ph = str(x)
            for user_def_field in ff_index:
                exec("value_" + str(user_def_field) + " = field_index_" + str(user_def_field) + "[" + ph + "]")
                exec("value__" + str(user_def_field) + " = (float(value_" + str(user_def_field)
                     + ")) * (float(user_weights[" + str(counter_x) + "]))")
                exec("composite_value += value__" + str(user_def_field))
                exec("counter_x += 1")
            exec("composite_list.append(composite_value)")

        # Reference The Vector Layer In Focus
        lyrOutput = QgsVectorLayer(file_path, name + "_MCDA", "ogr")
        provider = lyrOutput.dataProvider()

        # Add A new Column To The Vector File
        provider.addAttributes([QgsField("Composite", QVariant.Double)])
        idx = len(field_names) - 1
        lyrOutput.updateFields()

        for comp in composite_list:
            new_values = {idx: float(comp)}
            provider.changeAttributeValues({composite_list.index(comp): new_values})
        lyrOutput.commitChanges()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Simple MCDA'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    # -----------------------------------------------------------------------
    # This Is The Function That Does The Main Work Of The Plugin

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Set Variables
            self.setVariables()

            # Check To See If Variables & Weights Are Matching, If Everything Is Good Move On
            try:
                self.check_match()
            except:
                # Tell The User There Was Something Wrong
                iface.messageBar().pushMessage("Input Error!", "Inputs Do Not Match Up", duration=4)

            # Calculate New Field Based On Weights & Variables
            try:
                self.simple_mcda()
            except:
                # Tell The User There Was Something Wrong
                iface.messageBar().pushMessage("Input Error!", "Invalid Characters", duration=4)
