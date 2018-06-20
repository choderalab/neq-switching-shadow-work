"""
neq-switching-shadow-work
An exploration of the effect of shadow work on nonequilibrium switching relative free energy calculations
"""

# Make Python 2 and 3 imports work the same
# Safe to remove with Python 3-only code
from __future__ import absolute_import

# Add imports here
from .neq_switch_shadow_work import *

# Handle versioneer
from ._version import get_versions
versions = get_versions()
__version__ = versions['version']
__git_revision__ = versions['full-revisionid']
del get_versions, versions
