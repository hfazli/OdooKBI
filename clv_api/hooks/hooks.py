from odoo.api import Environment
from odoo.release import version_info

from .actions import after_install_action, before_uninstall_action
from ..wrappers.odoo_env_wrapper import OdooEnvWrapper


def post_install_hook(env: Environment) -> None:
    """
    Post-installation hook executed after the module is installed.
    Applicable to Odoo version 17 and above.
    """
    after_install_action(OdooEnvWrapper(env, version_info[0]))


def pre_uninstall_hook(env: Environment) -> None:
    """
    Pre-uninstallation hook executed before the module is uninstalled.
    Applicable to Odoo version 17 and above.
    """
    before_uninstall_action(OdooEnvWrapper(env, version_info[0]))
