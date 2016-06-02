from json import loads

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.lib.render
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as toolkit
import requests
from ckan.common import _, c
from ckan.controllers.package import PackageController
from ckan.lib.mailer import mail_recipient
from ckan.logic import clean_dict
from ckan.logic import parse_params
from ckan.logic import tuplize_dict
from ckan.model import Session
from lxml import etree
from lxml.builder import ElementMaker
from pylons import config
from pylons import request

from ckanext.ands.model import DoiRequest
from helpers import package_get_year

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
abort = base.abort
get_action = logic.get_action

render = base.render
lookup_package_plugin = ckan.lib.plugins.lookup_package_plugin

doi_request_fields = [
    'Paper Title',
    'Conference Or Journal Title',
    'Author List',
    'DOI Title',
    'DOI Description',
    'Message to Admin (Optional)'
]


def build_xml(dataset):
    author = dataset['author']

    publisher = config['ckanext.ands.publisher']
    # Dev prefix default
    doi_prefix = config.get('ckanext.ands.doi_prefix', '10.5072/')

    # TODO what should this be?
    ands_client_id = config['ckanext.ands.client_id']

    namespaces = {
        'xsi': "http://www.w3.org/2001/XMLSchema-instance",
        None: "http://datacite.org/schema/kernel-3",
    }

    Root = ElementMaker(
        nsmap=namespaces
    )
    E = ElementMaker()

    xml = Root.resource(
        E.identifier(doi_prefix + ands_client_id, identifierType="DOI"),
        E.creators(E.creator(E.creatorName(author))),
        E.titles(E.title(dataset['title'])),
        E.publisher(publisher),
        E.publicationYear("{}".format(package_get_year(dataset))),
        E.language('en'),
        E.resourceType('gDMCP Dataset', resourceTypeGeneral="Dataset"),
        E.descriptions(E.description(dataset['notes'], descriptionType="Abstract")),
    )

    xml.attrib[etree.QName(namespaces['xsi'],
                           'schemaLocation')] = "http://datacite.org/schema/kernel-3 http://schema.datacite.org/meta/kernel-3/metadata.xsd"

    return etree.tostring(xml, pretty_print=True)


def post_doi_request(dataset_url, contents):
    app_id = config['ckanext.ands.DOI_API_KEY']
    shared_secret = config['ckanext.ands.shared_secret']

    mint_service_url = (
        'https://services.ands.org.au/doi/1.1/mint.json/?app_id={}&url={}&debug={}'.format(
            app_id, dataset_url, config.get('ckanext.ands.debug', False)))

    #  Send data
    return requests.post(mint_service_url, data={'xml': contents, 'shared_secret': shared_secret})


def email_requestors(dataset_id):
    requests = Session.query(DoiRequest).filter_by(package_id=dataset_id)

    subject = 'DataPortal DOI Request approved'
    data = {
        'dataset_url': toolkit.url_for(
            controller='package',
            action='read',
            id=dataset_id,
            qualified=True)
    }

    body = base.render(
        'package/doi_request_completed.text',
        extra_vars=data)

    for request in requests:
        user = toolkit.get_action('user_show')(None, {'id': request.user_id})
        if user['email']:
            mail_recipient(user['display_name'], user['email'], subject, body)


class DatasetDoiController(PackageController):
    def fail_if_private(self, dataset, dataset_url):
        if dataset['private']:
            h.flash_error("Cannot add a DOI to a private dataset")
            toolkit.redirect_to(dataset_url)

    def dataset_doi(self, id):
        if request.method == 'POST':
            return self.handle_submit(id)
        else:
            return self.doi_form(id)

    def dataset_doi_admin(self, id):
        dataset_url = toolkit.url_for(
            controller='package',
            action='read',
            id=id,
            qualified=True
        )
        if not c.userobj.sysadmin:
            return toolkit.redirect_to(dataset_url)

        dataset = toolkit.get_action('package_show')(None, {'id': id})

        self.fail_if_private(dataset, dataset_url)

        if request.method == 'POST':
            return self.dataset_doi_admin_process(dataset_url, dataset)
        else:
            return self.dataset_doi_admin_form(dataset_url, dataset)

    def dataset_doi_admin_form(self, dataset_url, dataset):
        xml = build_xml(dataset)
        template = 'package/doi_admin.html'
        return render(template, extra_vars={'xml': xml, 'dataset_url': dataset_url})

    def dataset_doi_admin_process(self, dataset_url, dataset):
        # If running on local machine, just resolve DOI to the dev server
        if 'localhost' in dataset_url or '127.0.0.1' in dataset_url:
            xml_url = config.get('ckanext.ands.debug_url')
        else:
            xml_url = dataset_url

        post_data = request.POST['xml']

        resp = post_doi_request(xml_url, post_data)
        try:
            json = loads(resp.content)
        except ValueError as exp:
            h.flash_error("Invalid response from DOI server: {} :: {}".format(exp, resp.content))
            return toolkit.redirect_to(dataset_url)
        try:
            response_dict = json["response"]
        except KeyError:
            h.flash_error("Response had no response key: {}".format(json))
            return toolkit.redirect_to(dataset_url)

        doi = response_dict["doi"]
        response_code = response_dict["responsecode"]
        success_code = "MT001"

        if response_code == success_code:
            dataset['doi_id'] = doi
            toolkit.get_action('package_update')(None, dataset)

            email_requestors(dataset['id'])

            h.flash_success("DOI Created successfully")
        else:
            type = response_dict["type"]
            err_msg = response_dict["message"]
            verbose_msg = response_dict["verbosemessage"]
            msg = response_code + ' - ' + type + '. ' + verbose_msg + '. ' + err_msg
            h.flash_error(_(msg))

        return toolkit.redirect_to(dataset_url)

    def doi_form(self, id):
        # Mostly copied from PackageController:read
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        data_dict = {'id': id}
        dataset_url = toolkit.url_for(
            controller='package',
            action='read',
            id=id,
            qualified=True
        )

        # check if package exists
        try:
            c.pkg_dict = get_action('package_show')(context, data_dict)
            c.pkg = context['package']
        except NotFound:
            abort(404, _('Dataset not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read package %s') % id)

        self.fail_if_private(c.pkg_dict, dataset_url)

        # used by disqus plugin
        c.current_package_id = c.pkg.id
        c.related_count = c.pkg.related_count

        package_type = c.pkg_dict['type'] or 'dataset'
        self._setup_template_variables(context, {'id': id},
                                       package_type=package_type)

        ########################## ADD DOI STUFF ###########################
        template = 'package/doi.html'
        fields = dict(
            (field.lower().replace(' ', '_').translate(None, '()'), field)
            for field in doi_request_fields
        )

        q = Session.query(DoiRequest).filter_by(package_id=c.pkg_dict['id'], user_id=c.userobj.id)
        ((request_exists, ),) = Session.query(q.exists())
        if request_exists:
            h.flash_notice("You've already requested a DOI for this dataset. "
                            "You'll be emailed if it is approved.")
            return toolkit.redirect_to(dataset_url)

        try:
            return render(template,
                          extra_vars={
                              'dataset_type': package_type,
                              # TODO
                              'data': {},
                              'errors': None,
                              'fields': fields
                          })
        except ckan.lib.render.TemplateNotFound:
            msg = _("Viewing {package_type} datasets in {format} format is "
                    "not supported (template file {file} not found).".format(
                package_type=package_type, format=format,
                file=template))
            abort(404, msg)

    def handle_submit(self, id):
        data = clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
            request.params))))

        data['dataset_url'] = toolkit.url_for(
            controller='package',
            action='read',
            id=id,
            qualified=True
        )

        package = get_action('package_show')(None, {'id': id})
        self.fail_if_private(package, data['dataset_url'])

        # Comma separated config var
        to_addrs = config['ckanext.ands.support_emails'].split(',')

        subject = 'DataPortal Support: Request to publish dataset'

        body = base.render(
            'package/doi_email.text',
            extra_vars=data)

        for email in to_addrs:
            mail_recipient('Dataportal support', email, subject, body)

        data['package_id'] = package['id']
        data['user_id'] = c.userobj.id

        doi_request = DoiRequest(**data)
        Session.add(doi_request)
        Session.commit()

        h.flash_success("DOI Request sent")
        return toolkit.redirect_to(data['dataset_url'])
