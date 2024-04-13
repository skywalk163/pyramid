from pyramid.authorization import (
    Allow,
    Everyone,
)
from pyramid.httpexceptions import (
    HTTPNotFound,
    HTTPSeeOther,
)
import sqlalchemy as sa

from . import models


def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('view_wiki', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('view_page', '/{pagename}', factory=page_factory)
    config.add_route('add_page', '/add_page/{pagename}',
                     factory=new_page_factory)
    config.add_route('edit_page', '/{pagename}/edit_page',
                     factory=page_factory)

def new_page_factory(request):
    pagename = request.matchdict['pagename']
    exists = request.dbsession.execute(
        sa.select(sa.exists(models.Page)).where(models.Page.name == pagename)
    ).scalar()
    if exists:
        next_url = request.route_url('edit_page', pagename=pagename)
        raise HTTPSeeOther(location=next_url)
    return NewPage(pagename)

class NewPage:
    def __init__(self, pagename):
        self.pagename = pagename

    def __acl__(self):
        return [
            (Allow, 'role:editor', 'create'),
            (Allow, 'role:basic', 'create'),
        ]

def page_factory(request):
    pagename = request.matchdict['pagename']
    page = request.dbsession.scalars(
        sa.select(models.Page).where(models.Page.name == pagename)
    ).one_or_none()
    if page is None:
        raise HTTPNotFound
    return PageResource(page)

class PageResource:
    def __init__(self, page):
        self.page = page

    def __acl__(self):
        return [
            (Allow, Everyone, 'view'),
            (Allow, 'role:editor', 'edit'),
            (Allow, 'u:' + str(self.page.creator_id), 'edit'),
        ]
