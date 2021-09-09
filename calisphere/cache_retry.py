""" logic for cache / retry for solr and JSON from registry
"""

from future import standard_library
standard_library.install_aliases()
from builtins import object
from django.core.cache import cache
from django.conf import settings

from collections import namedtuple
import urllib.request, urllib.error, urllib.parse
from retrying import retry
import requests
import pickle
import hashlib
import json
import itertools
from typing import Dict, List, Tuple

requests.packages.urllib3.disable_warnings()

from aws_xray_sdk.core import patch

if hasattr(settings, 'XRAY_RECORDER'):
    patch(('requests', ))

# put this here for now
from elasticsearch import Elasticsearch

elastic_client = Elasticsearch(
    hosts=[settings.ES_HOST],
    http_auth=(settings.ES_USER, settings.ES_PASS))

ESResults = namedtuple(
    'ESResults', 'results numFound facet_counts')
ESItem = namedtuple(
    'ESItem', 'found, item, resp')


def ES_search(body):
    results = elastic_client.search(
        index="calisphere-items", body=body)

    aggs = results.get('aggregations')
    facet_counts = {'facet_fields': {}}
    if aggs:
        for facet_field in aggs:
            buckets = aggs[facet_field].get('buckets')
            facet_values = {b['key']: b['doc_count'] for b in buckets}
            facet_counts['facet_fields'][facet_field] = facet_values
    else:
        facet_counts = {}

    for result in results['hits']['hits']:
        metadata = result.pop('_source')
        metadata['title'] = [metadata.get('title')]
        metadata['type'] = [metadata.get('type')]
        metadata['type_ss'] = [metadata.get('type')]
        result.update(metadata)

    results = ESResults(
        results['hits']['hits'],
        results['hits']['total']['value'],
        facet_counts)

    return results


def ES_search_nocache(**kwargs):
    return ES_search(kwargs)


def ES_get(item_id):
    item_search = elastic_client.get(
        index="calisphere-items", id=item_id)
    found = item_search['found']
    item = item_search['_source']

    # make it look a little more like solr
    item.pop('word_bucket')
    item['title'] = [item['title']]
    item['type'] = [item['type']]
    item['source'] = [item['source']]
    item['location'] = [item['location']]

    results = ESItem(found, item, item_search)
    return results


SOLR_DEFAULTS = {
    'mm': '100%',
    'pf3': 'title',
    'pf': 'text,title',
    'qs': 12,
    'ps': 12,
}

SolrResults = namedtuple(
    'SolrResults', 'results header numFound facet_counts nextCursorMark')


def SOLR(**params):
    # replacement for edsu's solrpy based stuff
    solr_url = '{}/query/'.format(settings.SOLR_URL)
    solr_auth = {'X-Authentication-Token': settings.SOLR_API_KEY}
    # Clean up optional parameters to match SOLR spec
    query = {}
    for key, value in list(params.items()):
        key = key.replace('_', '.')
        query.update({key: value})
    res = requests.post(solr_url, headers=solr_auth, data=query, verify=False)
    res.raise_for_status()
    results = json.loads(res.content.decode('utf-8'))
    facet_counts = results.get('facet_counts', {})
    for key, value in list(facet_counts.get('facet_fields', {}).items()):
        # Make facet fields match edsu with grouper recipe
        facet_counts['facet_fields'][key] = dict(
            itertools.zip_longest(*[iter(value)] * 2, fillvalue=""))

    return SolrResults(
        results['response']['docs'],
        results['responseHeader'],
        results['response']['numFound'],
        facet_counts,
        results.get('nextCursorMark'),
    )


# create a hash for a cache key
def kwargs_md5(**kwargs):
    m = hashlib.md5()
    m.update(pickle.dumps(kwargs))
    return m.hexdigest()


# wrapper function for json.loads(urllib2.urlopen)
@retry(wait_exponential_multiplier=2, stop_max_delay=10000)  # milliseconds
def json_loads_url(url_or_req):
    key = kwargs_md5(key='json_loads_url', url=url_or_req)
    data = cache.get(key)
    if not data:
        try:
            data = json.loads(
                urllib.request.urlopen(url_or_req).read().decode('utf-8'))
        except urllib.error.HTTPError:
            data = {}
    return data


# dummy class for holding cached data
class SolrCache(object):
    pass


# wrapper function for solr queries
@retry(stop_max_delay=3000)  # milliseconds
def SOLR_select(**kwargs):
    kwargs.update(SOLR_DEFAULTS)
    # look in the cache
    key = 'SOLR_select_{0}'.format(kwargs_md5(**kwargs))
    sc = cache.get(key)
    if not sc:
        # do the solr look up
        sr = SOLR(**kwargs)
        # copy attributes that can be pickled to new object
        sc = SolrCache()
        sc.results = sr.results
        sc.header = sr.header
        sc.facet_counts = getattr(sr, 'facet_counts', None)
        sc.numFound = sr.numFound
        cache.set(key, sc, settings.DJANGO_CACHE_TIMEOUT)  # seconds
    return sc


@retry(stop_max_delay=3000)
def SOLR_raw(**kwargs):
    kwargs.update(SOLR_DEFAULTS)
    # look in the cache
    key = 'SOLR_raw_{0}'.format(kwargs_md5(**kwargs))
    sr = cache.get(key)
    if not sr:
        # do the solr look up
        solr_url = '{}/query/'.format(settings.SOLR_URL)
        solr_auth = {'X-Authentication-Token': settings.SOLR_API_KEY}
        # Clean up optional parameters to match SOLR spec
        query = {}
        for key, value in list(kwargs.items()):
            key = key.replace('_', '.')
            query.update({key: value})
        res = requests.get(
            solr_url, headers=solr_auth, params=query, verify=False)
        res.raise_for_status()
        sr = res.content
        cache.set(key, sr, settings.DJANGO_CACHE_TIMEOUT)  # seconds
    return sr


@retry(stop_max_delay=3000)
def SOLR_select_nocache(**kwargs):
    kwargs.update(SOLR_DEFAULTS)
    sr = SOLR(**kwargs)
    return sr


FieldName = str
Order = str
FilterValues = list
FilterField = Dict[FieldName, FilterValues]
Filters = List[FilterField]


def query_encode(query_string: str = None, 
                 filters: Filters = None,
                 exclude: Filters = None,
                 sort: Tuple[FieldName, Order] = None,
                 start: int = None,
                 rows: int = 0,
                 result_fields: List[str] = None,
                 facets: List[str] = None,
                 facet_sort: dict = None):

    es_params = {}

    es_query = es_filters = es_exclude = None

    if query_string:
        es_query = [{
            "query_string": {
                "query": query_string
            }
        }]

    if filters:
        es_filters = [{
            'terms': {k: v} for k, v in f.items()
        } for f in filters]

    if exclude:
        es_exclude = [{
            'terms': {k: v} for k, v in e.items()
        } for e in exclude]

    if es_query or es_filters or es_exclude:
        es_params['query'] = {'bool': {}}
        if es_query:
            es_params['query']['bool']['must'] = es_query
        if es_filters:
            es_params['query']['bool']['filter'] = es_filters
        if es_exclude:
            es_params['query']['bool']['must_not'] = es_exclude

        # unsure if this is an unnecessary optimization:
        # https://discuss.elastic.co/t/filter-performance-difference-bool-vs-terms/59928
        if len(es_params['query']['bool']) == 1:
            if 'must' in es_params['query']['bool']:
                es_params['query'] = es_query[0]
            elif ('filter' in es_params['query']['bool'] and 
                  len(es_params['query']['bool']['filter']) == 1):
                es_params['query'] = es_filters[0]

    if facets:
        exceptions = ['collection_ids', 'repository_ids', 'campus_ids']
        aggs = {}
        for facet in facets:
            if facet in exceptions or facet[-8:] == '.keyword':
                field = facet
            else:
                field = f'{facet}.keyword'

            aggs[facet] = {
                "terms": {
                    "field": field,
                    "size": 10000
                }
            }

            if facet_sort:
                aggs[facet]["terms"]["order"] = facet_sort
        # regarding 'size' parameter here and getting back all the facet values
        # please see: https://github.com/elastic/elasticsearch/issues/18838

        es_params.update({"aggs": aggs})

    if result_fields:
        es_params.update({"_source": result_fields})

    # if sort:
    #     es_params.update({
    #         "sort": [{
    #             sort[0]: {"order": sort[1]}
    #         }]
    #     })
    
    es_params.update({'size': rows})
    if start:
        es_params.update({'from': start})
    return es_params


def search_index(query):
    return ES_search(query_encode(**query))
