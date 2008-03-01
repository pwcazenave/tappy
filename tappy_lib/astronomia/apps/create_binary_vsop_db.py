#! /usr/bin/env python

"""Copyright 2000, 2001 William McClain

    This file is part of Astrolabe.

    Astrolabe is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Astrolabe is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Astrolabe; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
    """

"""Create a binary version of the VSOP87d database.

Usage:

    ./create_binary_vsop_db.py 
        
"""
from astronomia.util import load_params
from astronomia.vsop87d import load_vsop87d_text_db, write_vsop87d_binary_db

load_params()
print "reading text database..."
load_vsop87d_text_db()
print "writing binary database..."
write_vsop87d_binary_db()
