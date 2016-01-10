# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GreenSpace
                                 A QGIS plugin
 This tool can be used to support green area planning in the built environment.
                             -------------------
        begin                : 2015-12-03
        copyright            : (C) 2015 by Rob Braggaar, IJsbrand Groeneveld and Brenda Olsen
        email                : -
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GreenSpace class from file GreenSpace.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .green_space import GreenSpace
    return GreenSpace(iface)
