import logging
import re
from django.conf import settings

from itertools import zip_longest
from .cache_retry import SOLR_select, json_loads_url
from calisphere.collection_data import CollectionManager
from .constants import collection_template, collection_regex

logger = logging.getLogger(__name__)

def getCollectionIdFromUrl(url):
	match = re.match(collection_regex, url)
	if match is None:
		logger.warning("No collection ID found in url: {0}".format(url))
		return None
	else:
		return match.group('id')


def process_sort_collection_data(string):
    '''temporary; should parse sort_collection_data
       with either `:` or `::` dlimiter style
    '''
    if '::' in string:
        return string.split('::', 2)
    else:
        part1, remainder = string.split(':', 1)
        part2, part3 = remainder.rsplit(':https:')
        return [part1, part2, 'https:{}'.format(part3)]


def parseCollectionData(collection_data):
	""" parses solr's collection_data value
	returns { 'url', 'name', 'id' }"""
	data = collection_data.split('::')
	keys = ['url', 'name']
	collection = dict(zip_longest(keys, data, fillvalue=''))

	collection['id'] = getCollectionIdFromUrl(collection['url'])
	if collection['id'] is None:
		logger.warning("Bad collection url in solr collection_data"
					   " field: {0}".format(collection_data))
		collection['id'] = ''

	return collection


def getFullCollection(url, collection_data = None):
	""" takes a collection url and returns all collection metadata
	optionally takes a collection_data string as an additional data
	source in aggregating full collection details"""

	collection = {
		'id': getCollectionIdFromUrl(url),
		'url': url
	}
	registry_collection = json_loads_url("{0}?format=json".format(url))

	# get the collection name
	if collection_data:
		collection['name'] = parseCollectionData(collection_data).get('name')
	else:
		solr_collections = CollectionManager(settings.SOLR_URL,
											 settings.SOLR_API_KEY)
		collection['name'] = solr_collections.names.get(collection['url']
			) or registry_collection.get('name', '[no collection name]')
	
	# get all other collection metadata from the registry
	collection['description'] = registry_collection.get('description')
	collection['local_id'] = registry_collection.get('local_id')
	collection['slug'] = registry_collection.get('slug')
	collection['harvest_type'] = registry_collection.get('harvest_type')
	collection['custom_facet'] = registry_collection.get('custom_facet')

	collection_repositories = []
	for repository in registry_collection.get('repository'):
		if 'campus' in repository and len(repository['campus']) > 0:
			collection_repositories.append(repository['campus'][0]['name'] +
										   ", " + repository['name'])
		else:
			collection_repositories.append(repository['name'])
	collection['repositories'] = collection_repositories

	if ((settings.UCLDC_FRONT == 'https://calisphere.org/') or 
		(settings.UCLDC_DISQUS == 'prod')):
		collection['disqus_shortname'] = registry_collection.get(
			'disqus_shortname_prod')
	else:
		collection['disqus_shortname'] = registry_collection.get(
			'disqus_shortname_test')

	return collection


def getCollectionData(collection_data=None, collection_id=None):
	collection = {}
	if collection_data:
		parts = collection_data.split('::')
		collection['url'] = parts[0] if len(parts) >= 1 else ''
		collection['name'] = parts[1] if len(parts) >= 2 else ''
		collection_api_url = re.match(
			r'^https://registry\.cdlib\.org/api/v1/collection/(?P<url>\d*)/?',
			collection['url'])
		if collection_api_url is None:
			print('no collection api url:')
			collection['id'] = ''
		else:
			collection['id'] = collection_api_url.group('url')
	elif collection_id:
		solr_collections = CollectionManager(settings.SOLR_URL,
											 settings.SOLR_API_KEY)
		collection[
			'url'] = "https://registry.cdlib.org/api/v1/collection/{0}/".format(
				collection_id)
		collection['id'] = collection_id
		collection_details = json_loads_url(
			"{0}?format=json".format(collection['url']))

		collection['name'] = solr_collections.names.get(collection['url']
			) or collection_details.get('name', '[no collection name]')

		collection['local_id'] = collection_details.get('local_id')
		collection['slug'] = collection_details.get('slug')
	return collection


def getCollectionMosaic(collection_url):
    # get collection information from collection registry
    collection_details = getFullCollection(collection_url)

    # get 6 image items from the collection for the mosaic preview
    search_terms = {
        'q': '*:*',
        'fields': 'reference_image_md5, url_item, id, title, collection_url, type_ss',
        'sort': 'sort_title asc',
        'rows': 6,
        'start': 0,
        'fq': [
            'collection_url: \"' + collection_url + '\"', 'type_ss: \"image\"'
        ]
    }
    display_items = SOLR_select(**search_terms)
    items = display_items.results
    numFound = display_items.numFound

    # if there's not enough image items, get some non-image items for the mosaic preview
    if len(items) < 6:
        search_terms['fq'] = [
            'collection_url: \"' + collection_url + '\"',
            '(*:* AND -type_ss:\"image\")'
        ]
        ugly_display_items = SOLR_select(**search_terms)

        items = items + ugly_display_items.results
        numFound = numFound + ugly_display_items.numFound

    return {
        'name': collection_details['name'],
        'description': collection_details['description'],
        'collection_id': collection_details['id'],
        'institutions': collection_details['repositories'],
        'numFound': numFound,
        'display_items': items
    }