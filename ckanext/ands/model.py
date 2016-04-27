from ckan.model import meta, Package
from ckan.model.domain_object import DomainObject
from sqlalchemy import Table, Column, types, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relation, backref

doi_request_table = Table(
    'doi_requests', meta.metadata,
    Column('id', types.Integer, primary_key=True),

    Column(
        'package_id', types.UnicodeText,
        ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False),
    Column(
        'user_id', types.UnicodeText,
        ForeignKey('user.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False),
    UniqueConstraint('package_id', 'user_id'),

    Column('paper_title', types.UnicodeText, nullable=True),
    Column('conference_or_journal_title', types.UnicodeText, nullable=True),
    Column('author_list', types.UnicodeText, nullable=True),
    Column('doi_title', types.UnicodeText, nullable=True),
    Column('doi_description', types.UnicodeText, nullable=True),
    Column('message_to_admin_optional', types.UnicodeText, nullable=True),

)


class DoiRequest(DomainObject):
    """
    DOI Request
    """
    pass

meta.mapper(DoiRequest, doi_request_table, properties={
    'dataset': relation(
        Package,
        backref=backref('doi_request', cascade='all, delete-orphan'),
        primaryjoin=doi_request_table.c.package_id.__eq__(Package.id)
    )
})