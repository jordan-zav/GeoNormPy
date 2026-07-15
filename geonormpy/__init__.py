# Copyright (c) 2026 Jordan Zavaleta
# This file is part of GeoNormPy.
# GeoNormPy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
GeoNormPy public package exports.
"""

from .schema import DIAGNOSTIC_COLUMNS, ID_COLUMNS, OXIDE_COLUMNS

__version__ = "0.1.1"

__all__ = ["ID_COLUMNS", "OXIDE_COLUMNS", "DIAGNOSTIC_COLUMNS", "__version__"]
