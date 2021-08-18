from future import standard_library
from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from django.http import Http404, JsonResponse
from calisphere.collection_data import CollectionManager
from . import constants
from .facet_filter_type import FacetFilterType
from .cache_retry import json_loads_url, elastic_client
from .search_form import CollectionForm, solr_escape
from builtins import range

import os
import math
import string
import urllib.parse


standard_library.install_aliases()

col_regex = (r'https://registry\.cdlib\.org/api/v1/collection/'
             r'(?P<id>\d*)/?')
col_template = "https://registry.cdlib.org/api/v1/collection/{0}/"


def collections_directory(request):
    solr_collections = CollectionManager(settings.SOLR_URL,
                                         settings.SOLR_API_KEY)
    collections = []

    page = int(request.GET['page']) if 'page' in request.GET else 1

    for collection_link in solr_collections.shuffled[(page - 1) * 10:page *
                                                     10]:
        # col_id = re.match(col_regex, collection_link.url).group('id')
        col_id = collection_link.url
        try:
            collections.append(Collection(col_id).get_mosaic())
        except Http404:
            continue

    context = {
        'meta_robots': None,
        'collections': collections,
        'random': True,
        'pages': int(
            math.ceil(len(solr_collections.shuffled) / 10))
    }

    if page * 10 < len(solr_collections.shuffled):
        context['next_page'] = page + 1
    if page - 1 > 0:
        context['prev_page'] = page - 1

    return render(
        request,
        'calisphere/collections/collectionsRandomExplore.html',
        context
    )


def collections_az(request, collection_letter):
    solr_collections = CollectionManager(settings.SOLR_URL,
                                         settings.SOLR_API_KEY)
    collections_list = solr_collections.split[collection_letter.lower()]

    page = int(request.GET['page']) if 'page' in request.GET else 1
    pages = int(math.ceil(len(collections_list) / 10))

    collections = []
    for collection_link in collections_list[(page - 1) * 10:page * 10]:
        # col_id = re.match(col_regex, collection_link.url).group('id')
        col_id = collection_link.url
        try:
            collections.append(Collection(col_id).get_mosaic())
        except Http404:
            continue

    alphabet = list((character, True if character.lower() not in
                     solr_collections.no_collections else False)
                    for character in list(string.ascii_uppercase))

    context = {
        'collections': collections,
        'alphabet': alphabet,
        'collection_letter': collection_letter,
        'page': page,
        'pages': pages,
        'random': None,
    }

    if page * 10 < len(collections_list):
        context['next_page'] = page + 1
    if page - 1 > 0:
        context['prev_page'] = page - 1

    return render(request, 'calisphere/collections/collectionsAZ.html',
                  context)


def collections_titles(request):
    '''create JSON/data for the collections search page'''

    def djangoize(uri):
        '''turn registry URI into URL on django site'''
        # collection_id = uri.split(
        #     'https://registry.cdlib.org/api/v1/collection/', 1)[1][:-1]
        collection_id = uri
        return reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': collection_id})

    collections = CollectionManager(settings.SOLR_URL, settings.SOLR_API_KEY)
    data = [{
        'uri': djangoize(uri),
        'title': title
    } for (uri, title) in collections.parsed]
    return JsonResponse(data, safe=False)


def collections_search(request):
    return render(
        request,
        'calisphere/collections/collectionsTitleSearch.html',
        {
            'collections': [],
            'collection_q': True
        }
    )


class Collection(object):

    def __init__(self, collection_id):
        self.id = collection_id
        self.url = col_template.format(collection_id)
        self.details = json_loads_url(f"{self.url}?format=json")
        if not self.details:
            raise Http404(f"{collection_id} does not exist.")

        for repo in self.details.get('repository'):
            repo['resource_id'] = repo.get('resource_uri').split('/')[-2]

        self.custom_facets = self._parse_custom_facets()
        self.custom_schema_facets = self._generate_custom_schema_facets()

        self.solr_filter = 'collection_url: "' + self.url + '"'
        self.es_filter = {'collection_ids': [self.id]}

    def _parse_custom_facets(self):
        custom_facets = []
        if self.details.get('custom_facet'):
            for custom_facet in self.details.get('custom_facet'):
                custom_facets.append(
                    FacetFilterType(
                        None,
                        type={
                            'form_name': custom_facet['facet_field'],
                            'solr_facet_field': custom_facet['facet_field'],
                            'display_name': custom_facet['label'],
                            'solr_filter_field': custom_facet['facet_field'],
                            'sort_by': 'count',
                            'faceting_allowed': True
                        }
                    )
                )
        return custom_facets

    def _generate_custom_schema_facets(self):
        custom_schema_facets = [fd for fd in constants.UCLDC_SCHEMA_FACETS
                                if fd.facet != 'spatial']
        if self.custom_facets:
            for custom in self.custom_facets:
                for i, facet in enumerate(custom_schema_facets):
                    if custom.solr_facet_field == f"{facet.facet}_ss":
                        custom_schema_facets[i] = constants.FacetDisplay(
                            facet.facet, custom.display_name)
        return custom_schema_facets

    def get_summary_data(self):
        if hasattr(self, 'summary'):
            return self.summary

        summary_url = os.path.join(
            settings.UCLDC_METADATA_SUMMARY,
            '{}.json'.format(self.id),
        )
        self.summary = json_loads_url(summary_url)
        if not self.summary:
            raise Http404(f"{self.id} does not have summary data")

        self.item_count = self.summary['item_count']
        return self.summary

    def get_item_count(self):
        if hasattr(self, 'item_count'):
            return self.item_count

        es_params = {
            "query": {
                "term": {
                    "collection_ids": self.id
                }
            },
            "size": 0
        }
        es_search = elastic_client.search(
            index="calisphere-items", body=es_params)
        self.item_count = es_search.get('hits').get('total').get('value')
        return self.item_count

    def _choose_facet_sets(self, facet_set):
        if not facet_set:
            return False
        if len(facet_set['values']) < 1:
            return False

        # # exclude homogenous facet values;
        # ie: all 10 records have type: image
        # if (len(facet_set['values']) == 1 and
        #         facet_set['values'][0]['count'] == self.item_count):
        #     # although technically, this could mean that
        #     # 8 records have type: [image]
        #     # 1 record has type: [image, image]
        #     # 1 record has type: None
        #     return False

        # # exclude completely unique facet values
        # if facet_set['values'][0]['count'] == 1:
        #     return False

        return True

    def get_facet_sets(self):
        facet_sets = self.get_facets(self.custom_schema_facets)

        # choose facet sets to show
        chosen_facet_sets = [facet_set for facet_set in facet_sets
                             if self._choose_facet_sets(facet_set)]
        facet_sets = chosen_facet_sets

        return facet_sets

    def get_facets(self, facet_fields):
        es_params = {
            "query": {
                "term": {
                    'collection_ids': self.id
                }
            },
            "size": 0,
            "aggs": {}
        }
        for ff in facet_fields:
            es_params['aggs'][ff.facet] = {
                "terms": {
                    "field": f'{ff.facet}.keyword',
                    "size": 10000
                }
            }
        # regarding 'size' parameter here and getting back all the facet values
        # please see: https://github.com/elastic/elasticsearch/issues/18838
        es_search = elastic_client.search(
            index="calisphere-items", body=es_params)
        self.item_count = es_search.get('hits').get('total').get('value')
        # print(es_search.get('aggregations'))
        
        facets = []
        for facet_field in facet_fields:
            values = es_search.get('aggregations').get(facet_field.facet).get(
                'buckets')
            # make it look like solr
            values = {v['key']: v['doc_count'] for v in values}
            # values = solr_search.facet_counts.get('facet_fields').get(
            #     '{}_ss'.format(facet_field.facet))
            if not values:
                facets.append(None)

            unique = len(values)
            records = sum(values.values())

            values = [{'label': k, 'count': v, 'uri': reverse(
                'calisphere:collectionFacetValue',
                kwargs={
                    'collection_id': self.id,
                    'cluster': facet_field.facet,
                    'cluster_value': urllib.parse.quote_plus(k),
                })} for k, v in values.items()]

            facets.append({
                'facet_field': facet_field,
                'records': records,
                'unique': unique,
                'values': values
            })

        return facets

    def get_mosaic(self):
        repositories = []
        for repository in self.details.get('repository'):
            if 'campus' in repository and len(repository['campus']) > 0:
                repositories.append(repository['campus'][0]['name'] +
                                    ", " + repository['name'])
            else:
                repositories.append(repository['name'])

        es_search_terms = {
            "query": {
                "bool": {
                    "filter": [
                        {"terms": {"collection_ids": [self.id]}}, 
                        {"terms": {"type.keyword": ["image"]}}
                    ]
                }
            },
            "_source": [
                "reference_image_md5", 
                "url_item", 
                "calisphere-id", 
                "title", 
                "collection_ids", 
                "type"
            ],
            "sort": [{
                "title.keyword": {"order": "asc"}
            }], 
            "size": 6,
            "from": 0
        }

        display_items = elastic_client.search(
            index="calisphere-items", body=es_search_terms)
        items = display_items['hits']['hits']

        es_search_terms['query']['bool']['filter'].pop(1)
        es_search_terms['query']['bool']['must_not'] = [{
            "terms": {"type.keyword": ["image"]}
        }]

        ugly_display_items = elastic_client.search(
            index="calisphere-items", body=es_search_terms)

        # if there's not enough image items, get some non-image
        # items for the mosaic preview
        if len(items) < 6:
            items = items + ugly_display_items['hits']['hits']

        num_found = (
            display_items['hits']['total']['value'] + 
            ugly_display_items['hits']['total']['value'])

        return {
            'name': self.details['name'],
            'description': self.details['description'],
            'collection_id': self.id,
            'institutions': repositories,
            'numFound': num_found,
            'display_items': items
        }

    def get_lockup(self, keyword_query):
        rc_es_params = {
            "query": {
                "bool": {
                    "filter": [
                        {"terms": {"collection_ids": [self.id]}}, 
                    ]
                }
            },
            "_source": [
                "reference_image_md5", 
                "url_item", 
                "calisphere-id", 
                "title", 
                "collection_data", 
                "type"
            ],
            "sort": [{
                "title.keyword": {"order": "asc"}
            }], 
            "size": 3,
            "from": 0
        }

        if keyword_query:
            es_query_string = {
                "must": [{
                    "query_string": {
                        "query": keyword_query
                    }
                }]
            }
            rc_es_params['query']['bool'].update(es_query_string)

        collection_items = elastic_client.search(
            index="calisphere-items", body=rc_es_params)
        collection_items = collection_items['hits']['hits']

        if len(collection_items) < 3:
            # redo the query without any search terms
            rc_es_params['query']['bool'].pop('must')
            collection_items_no_query = elastic_client.search(
                index="calisphere-items", body=rc_es_params)
            collection_items = (
                collection_items + collection_items_no_query['hits']['hits'])

        if len(collection_items) <= 0:
            # throw error
            print('no related collection items')

        repositories = []
        for repo in self.details.get('repository'):
            if 'campus' in repo and len(repo['campus']) > 0:
                repositories.append(repo['campus'][0]['name'] +
                                    ", " + repo['name'])
            else:
                repositories.append(repo['name'])

        return {
            'image_urls': collection_items,
            'name': self.details['name'],
            'collection_id': self.id,
            'institution': (', ').join(repositories)
        }

    def item_view(self):
        production_disqus = (
            settings.UCLDC_FRONT == 'https://calisphere.org/' or
            settings.UCLDC_DISQUS == 'prod'
        )
        if production_disqus:
            disqus_shortname = self.details.get(
                'disqus_shortname_prod')
        else:
            disqus_shortname = self.details.get(
                'disqus_shortname_test')

        return {
            "url": self.url,
            "name": self.details.get('name'),
            "id": self.id,
            "local_id": self.details.get('local_id'),
            "slug": self.details.get('slug'),
            "harvest_type": self.details.get('harvest_type'),
            "custom_facet": self.details.get('custom_facet'),
            "disqus_shortname": disqus_shortname
        }


def collection_search(request, collection_id):
    collection = Collection(collection_id)

    form = CollectionForm(request, collection)
    results = form.search()
    filter_display = form.filter_display()

    if settings.UCLDC_FRONT == 'https://calisphere.org/':
        browse = False
    else:
        browse = collection.get_facet_sets()

    context = {
        'q': form.q,
        'search_form': form.context(),
        'facets': form.get_facets(collection.es_filter),
        'pages': int(math.ceil(results.numFound / int(form.rows))),
        'numFound': results.numFound,
        'search_results': results.results,
        'filters': filter_display,
        'browse': browse,
        'meta_robots': None,
        'totalNumItems': collection.get_item_count(),
        'collection':
        collection.details,
        'collection_id':
        collection_id,
        'form_action':
        reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': collection_id}),
    }

    return render(
        request, 'calisphere/collections/collectionView.html', context)


def collection_facet(request, collection_id, facet):
    collection = Collection(collection_id)
    if facet not in [f.facet for f in constants.UCLDC_SCHEMA_FACETS]:
        raise Http404("{} is not a valid facet".format(facet))

    facet_type = [tup for tup in collection.custom_schema_facets
                  if tup.facet == facet][0]

    facets = collection.get_facets([facet_type])[0]
    if not facets:
        raise Http404("{0} has no facet values".format(facet))

    values = facets['values']
    if not values:
        raise Http404("{0} has no facet values".format(facet))

    sort = request.GET.get('sort', 'largestFirst')
    if sort == 'smallestFirst':
        values.reverse()
    if sort == 'az':
        values.sort(key=lambda v: v['label'])
    if sort == 'za':
        values.sort(key=lambda v: v['label'], reverse=True)

    view_format = request.GET.get('view_format', 'list')
    context = {}
    if view_format == 'grid':
        page = int(request.GET.get('page', 1))
        end = page * 24
        start = end - 24

        values = values[start:end]
        for value in values:
            escaped_cluster_value = solr_escape(value['label'])
            es_thumb_params = {
                "query": {
                    "bool": {
                        "filter": [
                            {"terms": {"collection_ids": [collection.id]}},
                            {"terms": {f"{facet}.keyword": [escaped_cluster_value]}}
                        ]
                    }
                },
                "_source": ["reference_image_md5, type_ss"],
                "size": 3
            }
            es_thumbs = elastic_client.search(
                index="calisphere-items", body=es_thumb_params)
            value['thumbnails'] = es_thumbs['hits']['hits']

        context.update({
            'page_info':
            {
                'page': page,
                'start': start+1,
                'end': end
            }
        })

    context.update({
        'q': request.GET.get('q', ''),
        'sort': sort,
        'view_format': view_format,
        'facet': facet_type,
        'values': values,
        'unique': facets['unique'],
        'records': facets['records'],
        'ratio': round((facets['unique'] / facets['records']) * 100, 2),
        'meta_robots': "noindex,nofollow",
        'description': None,
        'collection': collection.details,
        'collection_id': collection_id,
        'form_action': reverse(
            'calisphere:collectionFacet',
            kwargs={'collection_id': collection_id, 'facet': facet}),
        'item_count': collection.get_item_count(),
        'clusters': collection.get_facet_sets()
    })

    return render(
        request, 'calisphere/collections/collectionFacet.html', context)


def collection_facet_json(request, collection_id, facet):
    if facet not in [f.facet for f in constants.UCLDC_SCHEMA_FACETS]:
        raise Http404("{} is not a valid facet".format(facet))

    collection = Collection(collection_id)
    facets = collection.get_facets([constants.FacetDisplay(facet, 'json')])[0]
    if not facets:
        raise Http404("{0} has no facet values".format(facet))

    return JsonResponse(facets['values'], safe=False)


def collection_facet_value(request, collection_id, cluster, cluster_value):
    collection = Collection(collection_id)

    if cluster not in [f.facet for f in constants.UCLDC_SCHEMA_FACETS]:
        raise Http404("{} is not a valid facet".format(cluster))

    form = CollectionForm(request, collection)

    parsed_cluster_value = urllib.parse.unquote_plus(cluster_value)
    escaped_cluster_value = solr_escape(parsed_cluster_value)
    extra_filter = {f"{cluster}.keyword": [escaped_cluster_value]}

    results = form.search(extra_filter)

    if results.numFound == 1:
        return redirect(
            'calisphere:itemView',
            results.results[0]['_source']['calisphere-id'])

    collection_name = collection.details.get('name')
    context = {
        'search_form': form.context(),
        'search_results': results.results,
        'numFound': results.numFound,
        'pages': int(math.ceil(results.numFound / int(form.rows))),
        'facets': form.get_facets(collection.es_filter),
        'filters': form.filter_display(),
        'cluster': cluster,
        'cluster_value': parsed_cluster_value,
        'meta_robots': "noindex,nofollow",
        'collection': collection.details,
        'collection_id': collection_id,
        'title': (
            f"{cluster}: {parsed_cluster_value} "
            f"({results.numFound} items) from: {collection_name}"
        ),
        'description': None,
        'form_action': reverse(
            'calisphere:collectionFacetValue',
            kwargs={
              'collection_id': collection_id,
              'cluster': cluster,
              'cluster_value': cluster_value,
            }),
    }

    return render(
        request, 'calisphere/collections/collectionFacetValue.html', context)


def collection_metadata(request, collection_id):
    collection = Collection(collection_id)
    summary_data = collection.get_summary_data()

    context = {
        'title': f"Metadata report for {collection.details['name']}",
        'meta_robots': "noindex,nofollow",
        'description': None,
        'collection': collection.details,
        'collection_id': collection_id,
        'summary_data': summary_data,
        'UCLDC_SCHEMA_FACETS': constants.UCLDC_SCHEMA_FACETS,
        'form_action': reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': collection_id}),
    }

    return render(
        request, 'calisphere/collections/collectionMetadata.html', context)


def get_cluster_thumbnails(collection_id, facet, facet_value):
    escaped_cluster_value = solr_escape(facet_value)
    es_thumb_params = {
        "query": {
            "bool": {
                "filter": [
                    {"terms": {'collection_ids': [collection_id]}},
                    {"terms": {
                        f'{facet.facet}.keyword': [escaped_cluster_value]
                    }}
                ]
            }
        },
        "_source": ['reference_image_md5', 'type'],
        "size": 3
    }
    es_thumbs = elastic_client.search(
        index="calisphere-items", body=es_thumb_params)
    return es_thumbs['hits']['hits']

# average 'best case': http://127.0.0.1:8000/collections/27433/browse/
# long rights statement: http://127.0.0.1:8000/collections/26241/browse/
# questioning grid usefulness: http://127.0.0.1:8000/collections/26935/browse/
# grid is helpful for ireland, building, ruin, stone:
# http://127.0.0.1:8000/collections/12378/subject/?view_format=grid&sort=largestFirst
# failed browse page: http://127.0.0.1:8000/collections/10318/browse/
# failed browse page: http://127.0.0.1:8000/collections/26666/browse/
# known issue, no thumbnails: http://127.0.0.1:8000/collections/26666/browse/
# less useful thumbnails: http://127.0.0.1:8000/collections/26241/browse/


def collection_browse(request, collection_id):
    collection = Collection(collection_id)
    facet_sets = collection.get_facet_sets()

    if len(facet_sets) == 0:
        return redirect('calisphere:collectionView', collection_id)

    for facet_set in facet_sets:
        facet_set['thumbnails'] = get_cluster_thumbnails(
            collection.id,
            facet_set['facet_field'],
            facet_set['values'][0]['label']
        )

    context = {
        'meta_robots': "noindex,nofollow",
        'collection': collection.details,
        'collection_id': collection_id,
        'UCLDC_SCHEMA_FACETS': constants.UCLDC_SCHEMA_FACETS,
        'item_count': collection.get_item_count(),
        'clusters': facet_sets,
        'facet': None,
        'form_action': reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': collection_id}),
    }

    return render(
        request, 'calisphere/collections/collectionBrowse.html', context)


def get_rc_from_ids(rc_ids, rc_page, keyword_query):
    # get three items for each related collection
    three_related_collections = []
    rc_page = int(rc_page)
    for i in range(rc_page * 3, rc_page * 3 + 3):
        if len(rc_ids) <= i or not rc_ids[i]:
            break

        collection = Collection(rc_ids[i])
        lockup_data = collection.get_lockup(keyword_query)
        three_related_collections.append(lockup_data)

    return three_related_collections

