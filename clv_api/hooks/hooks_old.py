from odoo import api, SUPERUSER_ID
from odoo.api import Environment
from odoo.release import version_info

from .actions import before_uninstall_action, after_install_action
from ..wrappers.odoo_env_wrapper import OdooEnvWrapper


def post_install_hook(cr, registry) -> None:
    """
    Post-installation hook executed after the module is installed.
    Applicable to Odoo version 16 and earlier.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    after_install_action(OdooEnvWrapper(env, version_info[0]))


def pre_uninstall_hook(cr, registry) -> None:
    """
    Pre-uninstallation hook executed before the module is uninstalled.
    Applicable to Odoo version 16 and earlier.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    before_uninstall_action(OdooEnvWrapper(env, version_info[0]))
