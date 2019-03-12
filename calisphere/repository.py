import logging
import re
from django.apps import apps
from django.conf import settings

from itertools import zip_longest
from calisphere.collection_data import CollectionManager
from calisphere.constants import repository_template, repository_regex

logger = logging.getLogger(__name__)

def getRepositoryIdFromUrl(url):
    match = re.match(repository_regex, url)
    if match is None:
        logger.warning("No repository ID found in url: {0}".format(url))
        return None
    else:
        return match.group('id')


def parseRepositoryData(repository_data):
    """ parses solr's repository_data value
    returns { 'url', 'name', 'campus', 'id' }"""
    data = repository_data.split('::')
    keys = ['url', 'name', 'campus']
    repository = dict(zip_longest(keys, data, fillvalue=''))

    repository['id'] = getRepositoryIdFromUrl(repository['url'])
    if repository['id'] is None:
        logger.warning("Bad repository url in solr repository_data"
                       " field: {0}".format(repository_data))
        repository['id'] = ""

    return repository


def getFullRepository(url, repository_data = None):
    """ takes a repository url and returns all repository metadata
    optionally takes a repository_data string as an additional data
    source in aggregating full repository details"""

    repository = {
        'id': getRepositoryIdFromUrl(url),
        'url': url
    }

    app = apps.get_app_config('calisphere')
    registry_repo = app.registry.repository_data.get(int(repository['id']), {})

    # get repository['name']
    if repository_data:
        repository['name'] = parseRepositoryData(repository_data).get('name')
    else:
        repository['name'] = registry_repo.get('name')

    # get repository['campus'] and repository['slug'] from registry
    if ( 'campus' in registry_repo and 
         isinstance(registry_repo.get('campus'), list) and
         len(registry_repo.get('campus')) > 0 and
         'name' in registry_repo.get('campus')[0] ):
        repository['campus'] = registry_repo.get('campus')[0].get('name')

        if 'slug' in registry_repo.get('campus')[0]:
            repository['slug'] = "{0}-{1}".format(
                registry_repo.get('campus')[0].get('slug'),
                registry_repo.get('slug'))
    else:
        repository['campus'] = ''
        repository['slug'] = registry_repo.get('slug')

    # get all other repository metadata from the registry
    repository['ga_code'] = registry_repo.get('google_analytics_tracking_code')
    if settings.UCLDC_FRONT == 'https://calisphere.org/':
        repository['aeon_url'] = registry_repo.get('aeon_prod')
    else:
        repository['aeon_url'] = registry_repo.get('aeon_test')

    return repository


def getRepositoryData(repository_data=None, repository_id=None, repository_url=None):
    """ supply either `repository_data` from solr or the `repository_id` or `repository_url`
        all the reset will be looked up and filled in
    """
    app = apps.get_app_config('calisphere')
    repository = {}
    repository_details = {}
    if not (repository_data) and not (repository_id) and repository_url:
        repository_id = re.match(
            r'https://registry\.cdlib\.org/api/v1/repository/(?P<repository_id>\d*)/?',
            repository_url).group('repository_id')
    if repository_data:
        parts = repository_data.split('::')
        repository['url'] = parts[0] if len(parts) >= 1 else ''
        repository['name'] = parts[1] if len(parts) >= 2 else ''
        repository['campus'] = parts[2] if len(parts) >= 3 else ''

        repository_api_url = re.match(
            r'^https://registry\.cdlib\.org/api/v1/repository/(?P<url>\d*)/',
            repository['url'])
        if repository_api_url is None:
            print('no repository api url')
            repository['id'] = ''
        else:
            repository['id'] = repository_api_url.group('url')
            repository_details = app.registry.repository_data.get(
                int(repository['id']), {})
    elif repository_id:
        repository[
            'url'] = "https://registry.cdlib.org/api/v1/repository/{0}/".format(
                repository_id)
        repository['id'] = repository_id
        repository_details = app.registry.repository_data.get(
            int(repository_id), None)
        repository['name'] = repository_details['name']
        if repository_details['campus']:
            repository['campus'] = repository_details['campus'][0]['name']
        else:
            repository['campus'] = ''
    # details needed for stats
    repository['ga_code'] = repository_details.get(
        'google_analytics_tracking_code', None)

    production_aeon = settings.UCLDC_FRONT == 'https://calisphere.org/'
    if production_aeon:
        repository['aeon_url'] = repository_details.get('aeon_prod', None)
    else:
        repository['aeon_url'] = repository_details.get('aeon_test', None)
    parent = repository_details['campus']
    pslug = ''
    if len(parent):
        pslug = '{0}-'.format(parent[0].get('slug', None))
    repository['slug'] = pslug + repository_details.get('slug', None)
    return repository

