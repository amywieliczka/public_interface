import logging
import re
from itertools import zip_longest
from .cache_retry import json_loads_url
from calisphere.collection_data import CollectionManager

logger = logging.getLogger(__name__)

collection_template = "https://registry.cdlib.org/api/v1/collection/{0}/"
collection_regex = r'^https://registry\.cdlib\.org/api/v1/collection/(?P<id>\d*)/?'

def getCollectionIdFromUrl(url):
	match = re.match(collection_regex, url)
	if match is None:
		logger.warning("No collection ID found in url: {0}".format(url))
		return None
    else:
		return match.group('id')


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
		collection['name'] = [solr_collections].names.get(collection['url']
            ) or registry_collection.get('name', '[no collection name]')
	
	# get all other collection metadata from the registry
    collection['local_id'] = registry_collection.get('local_id')
    collection['slug'] = registry_collection.get('slug')
    collection['harvest_type'] = registry_collection.get('harvest_type')
    collection['custom_facet'] = registry_collection.get('custom_facet')

    if ((settings.UCLDC_FRONT == 'https://calisphere.org') or 
    	(settings.UCLDC_DISQUS == 'prod')):
        collection['disqus_shortname'] = registry_collection.get(
        	'disqus_shortname_prod')
    else:
        collection['disqus_shortname'] = registry_collection.get(
        	'disqus_shortname_test')

    return collection