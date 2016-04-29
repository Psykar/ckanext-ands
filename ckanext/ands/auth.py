import ckan.plugins.toolkit as toolkit
from ckan.logic.auth.delete import package_delete as default_package_delete


def package_delete(context, data_dict=None):
    if not context['auth_user_obj'].sysadmin:

        package = toolkit.get_action('package_show')(None, data_dict)

        if package.get('doi_id'):
            return {'success': False, 'msg': 'This dataset has a DOI so cannot be deleted'}

    return default_package_delete(context, data_dict=data_dict)
