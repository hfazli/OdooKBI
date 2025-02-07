from ..wrappers.odoo_env_wrapper import OdooEnvWrapper


def after_install_action(env: OdooEnvWrapper) -> None:
    """
    Actions performed after the module is installed.
    @param env: Odoo Environment object.
    """
    env.w15_settings.warehouse15_connected = False
    env.w15_settings.check_connection_failed = False

    env.w15_settings.default_scan_locations = True
    env.w15_settings.allow_only_lowest_level_locations = False
    env.w15_settings.auto_create_backorders = True
    env.w15_settings.scan_serials_on_allocation = True
    env.w15_settings.ship_expected_actual_lines = False


def before_uninstall_action(env: OdooEnvWrapper) -> None:
    """
    Actions performed before the module is uninstalled.
    @param env: Odoo Environment object.
    """
    env.w15_settings.unlink_all()
