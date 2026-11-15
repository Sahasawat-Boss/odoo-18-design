from . import models

HOME_ACTION = 'hrdi_home.action_hrdi_home'


def post_init_hook(env):
    """Make HRDI Home the landing page of internal users that have no home action yet."""
    action = env.ref(HOME_ACTION)
    users = env['res.users'].with_context(active_test=False).search([('share', '=', False), ('action_id', '=', False)])
    users.write({'action_id': action.id})


def uninstall_hook(env):
    action = env.ref(HOME_ACTION, raise_if_not_found=False)
    if action:
        env['res.users'].with_context(active_test=False).search([('action_id', '=', action.id)]).write({'action_id': False})
