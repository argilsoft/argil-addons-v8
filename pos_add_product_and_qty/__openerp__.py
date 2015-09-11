# -*- encoding: utf-8 -*-
###########################################################################
#    Copyright (c) 2015 Argil Consulting - http://www.argil.mx
#    info Argil Consulting (info@argil.mx)
############################################################################
#    Coded by: Israel Cruz (israel.cruz@argil.mx)
############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "POS - Add Product & Qty",
    "version": "1.0", 
    "author": "Argil", 
    "category": "POS", 
    "description": """
POS Add PRoduct & Qty greater than 1
====================================

Modulo para agregar el producto y la Cantidad mayor a 1

    """, 
    "website": "http://www.argil.mx", 
    "depends" : ["point_of_sale"],
    "data": ["pos_ticket_template.xml"],
    "qweb" : [
        'static/src/xml/pos_cb.xml',
    ], 
    "installable": True, 
    "active": False
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
