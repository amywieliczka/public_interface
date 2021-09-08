from django.test import Client
import unittest
from .cache_retry import query_encode
from .collection_views import Collection
from .institution_views import Repository, Campus
import re
# Create your tests here.


class CollectionQueriesTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_item_count(self):
        collection = Collection(466)
        es_params = {
            "filters": [collection.basic_filter],
            "rows": 0
        }
        es_params = query_encode(**es_params)
        manual_params = {
            "query": {'terms': {'collection_ids': [collection.id]}},
            "size": 0
        }
        self.assertEqual(es_params, manual_params)

    def test_get_facets(self):
        collection = Collection(466)
        facet_fields = collection.custom_schema_facets
        es_params = {
            "filters": [collection.basic_filter],
            "rows": 0,
            "facets": [ff.facet for ff in facet_fields]
        }
        encoded = query_encode(**es_params)
        manual_params = {
            "query": {'terms': {'collection_ids': [collection.id]}},
            "size": 0,
            "aggs": {}
        }
        for ff in facet_fields:
            manual_params['aggs'][ff.facet] = {
                "terms": {
                    "field": f'{ff.facet}.keyword',
                    "size": 10000
                }
            }
        self.assertEqual(encoded, manual_params)

    def test_get_mosaic(self):
        collection = Collection(466)
        es_params = {
            "filters": [
                collection.basic_filter,
                {"type.keyword": ["image"]}
            ],
            "result_fields": [
                "reference_image_md5",
                "url_item",
                "id",
                "title",
                "collection_ids",
                "type"
            ],
            "sort": ("title.keyword", "asc"),
            "rows": 6
        }
        es_params_encoded = query_encode(**es_params)

        search_terms = {
            "query": {
                "bool": {
                    "filter": [
                        {'terms': {'collection_ids': [collection.id]}} 
                        {"terms": {"type.keyword": ["image"]}}
                    ]
                }
            },
            "_source": [
                "reference_image_md5", 
                "url_item", 
                "id",
                "title", 
                "collection_ids", 
                "type"
            ],
            "sort": [{
                "title.keyword": {"order": "asc"}
            }],
            "size": 6
        }
        self.assertEqual(es_params_encoded, search_terms)

        es_params['filters'].pop(1)
        es_params['exclude'] = [{"type.keyword": ["image"]}]
        es_params = query_encode(**es_params)
        search_terms['query']['bool']['filter'].pop(1)
        search_terms['query']['bool']['must_not'] = [{
            "terms": {"type.keyword": ["image"]}
        }]
        self.assertEqual(es_params, search_terms)

    def test_get_lockup(self):
        collection = Collection(466)
        es_params = {
            'filters': [collection.basic_filter],
            'result_fields': [
                "reference_image_md5",
                "url_item",
                "id",
                "title",
                "collection_data",
                "type"
            ],
            'sort': ("title.keyword", "asc"),
            "rows": 3,
        }
        es_params_encoded = query_encode(**es_params)
        rc_params = {
            "query": {'terms': {'collection_ids': [collection.id]}},
            "_source": [
                "reference_image_md5", 
                "url_item", 
                "id",
                "title", 
                "collection_data", 
                "type"
            ],
            "sort": [{
                "title.keyword": {"order": "asc"}
            }], 
            "size": 3,
        }
        self.assertEqual(es_params_encoded, rc_params)

        keyword_query = "welcome"
        es_params['query_string'] = keyword_query
        es_params_encoded = query_encode(**es_params)
        es_query_string = {
            "bool": {
                "must": [{
                    "query_string": {
                        "query": keyword_query
                    }
                }],
                "filter": [{'terms': {'collection_ids': [collection.id]}}]
            }
        }
        rc_params['query'] = es_query_string
        self.assertEqual(es_params_encoded, rc_params)

        es_params.pop('query_string')
        es_params_encoded = query_encode(**es_params)
        rc_params['query'] = {'terms': {'collection_ids': [collection.id]}}
        self.assertEqual(es_params_encoded, rc_params)

    def test_collection_facet_thumb_params(self):
        collection = Collection(466)
        facet = "date"
        escaped_cluster_value = "October 17-18, 1991"
        es_params = {
            "filters": [
                collection.basic_filter, 
                {f"{facet}.keyword": [escaped_cluster_value]}
            ],
            "result_fields": ["reference_image_md5, type_ss"],
            "rows": 3
        }
        es_params = query_encode(**es_params)
        thumb_params = {
                "query": {
                    "bool": {
                        "filter": [
                            {'terms': {'collection_ids': [collection.id]}},
                            {"terms": {f"{facet}.keyword": [escaped_cluster_value]}}
                        ]
                    }
                },
                "_source": ["reference_image_md5, type_ss"],
                "size": 3
            }
        self.assertEqual(es_params, thumb_params)

    def test_get_cluster_thumbnails(self):
        collection = Collection(466)
        escaped_cluster_value = "AIDS (Disease)"
        facet = "subject"
        es_params = {
            'filters': [
                collection.basic_filter,
                {f'{facet}.keyword': [escaped_cluster_value]}
            ],
            'result_fields': ['reference_image_md5', 'type'],
            'rows': 3
        }
        es_params = query_encode(**es_params)
        thumb_params = {
            "query": {
                "bool": {
                    "filter": [
                        {'terms': {'collection_ids': [collection.id]}},
                        {"terms": {
                            f'{facet}.keyword': [escaped_cluster_value]
                        }}
                    ]
                }
            },
            "_source": ['reference_image_md5', 'type'],
            "size": 3
        }
        self.assertEqual(es_params, thumb_params)


class InstitutionQueriesTestCase(unittest.TestCase):
    def test_campus_directory(self):
        es_params = {
            "facets": ["repository_ids"]
        }
        es_params = query_encode(**es_params)
        repositories_query = {
            "size": 0,
            "aggs": {
                "repository_ids": {
                    "terms": {
                        "field": "repository_ids",
                        "size": 10000
                    }
                }
            }
        }
        self.assertEqual(es_params, repositories_query)

    def test_statewide_directory(self):
        es_params = {
            "facets": ["repository_ids"]
        }
        es_params = query_encode(**es_params)
        repositories_query = {
            "size": 0,
            "aggs": {
                "repository_ids": {
                    "terms": {
                        "field": "repository_ids",
                        "size": 10000
                    }
                }
            }
        }
        self.assertEqual(es_params, repositories_query)

    def test_institution_collections(self):
        institution = Repository(25)
        es_params = {
            'filters': [institution.basic_filter],
            'facets': ['collection_data'],
            'facet_sort': {"_key": "asc"}
        }
        es_params = query_encode(**es_params)
        collections_params = {
            "query": institution.filter,
            "size": 0,
            "aggs": {
                "collection_data": {
                    "terms": {
                        "field": "collection_data.keyword",
                        "size": 10000,
                        "order": {
                            "_key": "asc"
                        }
                    }
                }
            }
        }
        self.assertEqual(es_params, collections_params)

    def test_campus_institutions(self):
        institution = Campus('UCI')
        es_params = {
            'filters': [institution.basic_filter],
            'facets': ['repository_data']
        }
        es_params = query_encode(**es_params)
        institutions_search = {
            "query": {
                "terms": {
                    "campus_ids": [institution.id]
                }
            },
            "size": 0,
            "aggs": {
                "repository_data": {
                    "terms": {
                        "field": "repository_data.keyword",
                        "size": 10000
                    }
                }
            }
        }
        self.assertEqual(es_params, institutions_search)


class CollectionDataQueriesTestCase(unittest.TestCase):
    def test_get_collection_data(self):
        es_params = {
            'facets': ['collection_data']
        }
        es_params = query_encode(**es_params)
        collections_query = {
            "size": 0,
            "aggs": {
                "collection_data": {
                    "terms": {
                        "field": "collection_data.keyword",
                        "size": 10000
                    }
                }
            }
        }
        self.assertEqual(es_params, collections_query)


class ViewQueriesTestCase(unittest.TestCase):
    def test_item_view(self):
        item_id = "466--http:/example"

        def _fixid(id):
            return re.sub(r'^(\d*--http:/)(?!/)', r'\1/', id)

        es_params = {
            "query_string": f"harvest_id_s:*{_fixid(item_id)}",
            "rows": 10
        }
        es_params = query_encode(**es_params)
        old_id_search = {
            "query": {
                "query_string": {
                    "query": f"harvest_id_s:*{_fixid(item_id)}"
                }
            },
            "size": 10
        }
        self.assertEqual(es_params, old_id_search)

    def test_report_collection_facet(self):
        collection_id = 466
        facet = "subject"
        es_params = {
            "filters": [{'collection_ids': [collection_id]}],
            "facets": [facet]
        }
        es_params = query_encode(**es_params)

        collection_facet_query = {
            "query": {
                "terms": {'collection_ids': [collection_id]}
            },
            "size": 0,
            "aggs": {
                facet: {
                    "terms": {
                        "field": f'{facet}.keyword',
                        "size": 10000
                    }
                }
            }
        }
        self.assertEqual(es_params, collection_facet_query)


# c = Client()

# c.get('/')
# c.get('/exhibitions/')
