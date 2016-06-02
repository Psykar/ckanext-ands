import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.model import package_table

import helpers as h
from auth import package_delete
from model import doi_request_table


class AndsPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IDatasetForm, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.IAuthFunctions, inherit=True)

    # IConfigurable
    def configure(self, config):
        if package_table.exists():
            doi_request_table.create(checkfirst=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'ands')

    # IRoutes
    def after_map(self, map):
        map.connect(
            '/dataset/{id}/doi', action='dataset_doi',
            controller='ckanext.ands.controller:DatasetDoiController')
        map.connect(
            '/dataset/{id}/doi_approve', action='dataset_doi_admin',
            controller='ckanext.ands.controller:DatasetDoiController')
        return map

    # IDatasetForm
    def _modify_package_schema(self, schema):
        schema.update({
            'author': [toolkit.get_validator('not_empty'), unicode],
            'doi_id': [
                toolkit.get_converter('ignore_missing'),
                toolkit.get_converter('ignore_not_sysadmin'),
                toolkit.get_converter('convert_to_extras'),
            ]
        })
        return schema

    def create_package_schema(self):
        schema = super(AndsPlugin, self).create_package_schema()
        return self._modify_package_schema(schema)

    def update_package_schema(self):
        schema = super(AndsPlugin, self).update_package_schema()
        return self._modify_package_schema(schema)

    def show_package_schema(self):
        schema = super(AndsPlugin, self).show_package_schema()
        schema.update({
            'doi_id': [
                toolkit.get_converter('convert_from_extras'),
                toolkit.get_validator('ignore_missing')]
        })
        return schema

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    # IPackageController
    def edit(self, entity):
        # DOI key shouldn't be deleted!
        for extra in entity.extras_list:
            if extra.key == 'doi_id' and extra.value is not None:
                extra.state = 'active'

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'package_get_year': h.package_get_year,
            'now': h.now,
            'get_site_title': h.get_site_title,
            'can_request_doi': h.can_request_doi,
        }

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            'package_delete': package_delete
        }
