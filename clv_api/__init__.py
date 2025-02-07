# -*- coding: utf-8 -*-

from . import controllers
from . import models

from odoo.release import version_info
odoo_version = version_info[0]

if odoo_version >= 17:
    from .hooks.hooks import post_install_hook
    from .hooks.hooks import pre_uninstall_hook
else:
    from .hooks.hooks_old import post_install_hook
    from .hooks.hooks_old import pre_uninstall_hook
