#!/usr/bin/env python
# encoding: utf-8
"""
Created by 'bens3' on 2013-06-21.
Copyright (c) 2013 'bens3'. All rights reserved.
"""

from pylons import config
from datetime import datetime
import dateutil.parser as parser

from ckan.authz import has_user_permission_for_group_or_org
from ckan.plugins import toolkit


def package_get_year(pkg_dict):
    """
    Helper function to return the package year published
    @param pkg_dict:
    @return:
    """
    if not isinstance(pkg_dict['metadata_created'], datetime):
        pkg_dict['metadata_created'] = parser.parse(pkg_dict['metadata_created'])

    return pkg_dict['metadata_created'].year


def get_site_title():
    """
    Helper function to return the config site title, if it exists
    @return: str site title
    """
    return config.get("ckanext.doi.site_title")


def now():
    return datetime.now()


def can_request_doi(pkg):
    ''' Users can request a DOI if they are in the same org as the owner of the dataset '''
    userobj = toolkit.c.userobj
    owner_group_id = pkg['owner_org']
    if not userobj:
        return False
    if userobj.sysadmin:
        return True
    if pkg['creator_user_id'] == userobj.id:
        return True
    if owner_group_id is None:
        return False
    return has_user_permission_for_group_or_org(owner_group_id, userobj.name, 'read')
