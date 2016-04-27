"""Tests for plugin.py."""
import json
from datetime import datetime

import ckan
import requests
from ckan import model
from ckan.lib.helpers import url_for
from ckan.tests import factories
from ckan.tests import helpers
from ckan.tests.helpers import FunctionalTestBase, _get_test_app
from mock import Mock
from mock import call
from mock import patch
from nose.tools import assert_equal
from pylons import config

import ckanext.ands.controller
from ckanext.ands.controller import build_xml, post_doi_request, doi_request_fields

test_dataset_dict = {
    'author': 'An Author',
    'title': 'A dataset to do things with',
    'metadata_created': datetime.now(),
    'notes': 'Some notes about this dataset',
}


class TestAndsController(FunctionalTestBase):
    def __init__(self):
        self.app = None

    @classmethod
    def setup_class(cls):
        super(cls, cls).setup_class()
        helpers.reset_db()

    def teardown(self):
        ckan.plugins.unload('ands')

    def setup(self):
        self.app = _get_test_app()
        ckan.plugins.load('ands')

    def test_build_xml(self):
        # Mainly just check it works - no point checking lxml is working.
        build_xml(test_dataset_dict)

    def test_post_doi_request(self):
        test_dataset_url = 'http://blah.com'
        contents = ''
        with patch.object(requests, 'post') as mock_post:
            post_doi_request(test_dataset_url, contents)

        expected = [
            call('https://services.ands.org.au/doi/1.1/mint.json/?app_id=atestdoikey&url={}&debug=False'.format(
                test_dataset_url),
                data={'xml': contents, 'shared_secret': 'atestdoisecret'})]

        assert_equal(mock_post.mock_calls, expected)

    def test_dataset_has_doi_request_non_sysadmin(self):
        model.repo.rebuild_db()
        dataset = factories.Dataset(author='test author')
        response = self.app.get(url_for(
            controller='package', action='read',
            id=dataset['name']))
        response.mustcontain('Request DOI')
        response.mustcontain(no='Approve DOI')
        response.mustcontain(no='Cite this as')

    def test_dataset_has_doi_approve_sysadmin(self):
        model.repo.rebuild_db()
        dataset = factories.Dataset(author='test author')
        sysadmin = factories.Sysadmin()
        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        response = self.app.get(url_for(
            controller='package', action='read',
            id=dataset['name']), extra_environ=env)

        response.mustcontain('Request DOI')
        response.mustcontain('Approve DOI')
        response.mustcontain(no='Cite this as')

    def test_dataset_doi_admin_sysadmin(self):
        model.repo.rebuild_db()
        dataset = factories.Dataset(author='test author')
        sysadmin = factories.Sysadmin()
        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        url = url_for(
            controller='ckanext.ands.controller:DatasetDoiController', action='dataset_doi_admin',
            id=dataset['name'])
        mock_response = Mock(content=json.dumps(dict(response=dict(responsecode='MT001', doi='testdoi'))))
        mock_post = Mock(return_value=mock_response)
        with patch.object(requests, 'post', new=mock_post):
            response = self.app.post(url, extra_environ=env)

        # Don't bother checking the mocks, other tests do this

        response = response.follow(extra_environ=env)
        # Shouldn't appear as already created
        response.mustcontain(no='Approve DOI')
        response.mustcontain(no='Request DOI')
        response.mustcontain('Cite this as')

    def test_dataset_doi_admin_non_sysadmin(self):
        model.repo.rebuild_db()
        dataset = factories.Dataset(author='test author')
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        # Should redirect back to dataset page
        response = self.app.post(url_for(
            controller='ckanext.ands.controller:DatasetDoiController', action='dataset_doi_admin',
            id=dataset['name']), extra_environ=env)

        response = response.follow(extra_environ=env)
        response.mustcontain(no='Approve DOI')
        response.mustcontain(no='Cite this as')
        response.mustcontain('Request DOI')

    def test_dataset_doi_request(self):
        model.repo.rebuild_db()
        dataset = factories.Dataset(author='test author')
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        # Should redirect back to dataset page
        response = self.app.get(url_for(
            controller='ckanext.ands.controller:DatasetDoiController', action='dataset_doi',
            id=dataset['name']), extra_environ=env)
        for field in doi_request_fields:
            response.mustcontain(field)

        form = response.forms['dataset-doi']
        for field in form.fields:
            if field != 'save':
                form.set(field, 'test')

        with patch.object(ckanext.ands.controller, 'mail_recipient') as mock_mail:
            response = form.submit('submit', extra_environ=env)

        assert_equal(mock_mail.mock_calls, [call(
            'Dataportal support',
            config.get('ckanext.ands.support_emails'),
            'DataPortal Support: Request to publish dataset',
            u'A DOI has been requested\n\nDataset:  http://test.ckan.net/dataset/{}\n\n'
            u'Paper Title:  test\nConference Title: test\nAuthor List: test\nDOI Title: test\n'
            u'DOI Description: test\nOptional Message: test'.format(dataset['name']))])

    def test_approve_emails(self):
        model.repo.rebuild_db()
        dataset = factories.Dataset(author='test author')
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        # Should redirect back to dataset page
        response = self.app.get(url_for(
            controller='ckanext.ands.controller:DatasetDoiController', action='dataset_doi',
            id=dataset['name']), extra_environ=env)
        for field in doi_request_fields:
            response.mustcontain(field)

        form = response.forms['dataset-doi']
        for field in form.fields:
            if field != 'save':
                form.set(field, 'test')

        with patch.object(ckanext.ands.controller, 'mail_recipient') as mock_mail:
            response = form.submit('submit', extra_environ=env)

        assert_equal(mock_mail.mock_calls, [call(
            'Dataportal support',
            config.get('ckanext.ands.support_emails'),
            'DataPortal Support: Request to publish dataset',
            u'A DOI has been requested\n\nDataset:  http://test.ckan.net/dataset/{}\n\n'
            u'Paper Title:  test\nConference Title: test\nAuthor List: test\nDOI Title: test\n'
            u'DOI Description: test\nOptional Message: test'.format(dataset['name']))])

        # Now approve it
        sysadmin = factories.Sysadmin()
        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        url = url_for(
            controller='ckanext.ands.controller:DatasetDoiController', action='dataset_doi_admin',
            id=dataset['name'])
        mock_response = Mock(content=json.dumps(dict(response=dict(responsecode='MT001', doi='testdoi'))))
        mock_post = Mock(return_value=mock_response)
        with patch.object(requests, 'post', new=mock_post):
            with patch.object(ckanext.ands.controller, 'mail_recipient') as mock_mail:
                response = self.app.post(url, extra_environ=env)

        assert_equal(mock_mail.mock_calls, [
            call(u'Mr. Test User', u'test_user_0@ckan.org', 'DataPortal DOI Request approved',
                 u'A DOI you requested has been approved\n\nDataset:  http://test.ckan.net/dataset/{}'.format(
                     dataset['id']))])

        response = response.follow(extra_environ=env)
        # Shouldn't appear as already created
        response.mustcontain(no='Approve DOI')
        response.mustcontain(no='Request DOI')
        response.mustcontain('Cite this as')
