from .cache_retry import elastic_client
from . import constants
from django.http import Http404
from . import facet_filter_type as ff
from collections import namedtuple


def solr_escape(text):
    return text.replace('?', '\\?').replace('"', '\\"')


ESResults = namedtuple(
    'ESResults', 'results numFound facet_counts')


class SortField(object):
    default = 'relevance'
    no_keyword = 'a'

    def __init__(self, request):
        if (request.GET.get('q')
           or request.GET.getlist('rq')
           or request.GET.getlist('fq')):
            self.sort = request.GET.get('sort', self.default)
        else:
            self.sort = request.GET.get('sort', self.no_keyword)


class SearchForm(object):
    simple_fields = {
        'q': '',
        'rq': [],
        'rows': 24,
        'start': 0,
        'view_format': 'thumbnails',
        'rc_page': 0
    }
    sort_field = SortField
    facet_filter_fields = [
        ff.TypeFF,
        ff.DecadeFF,
        ff.RepositoryFF,
        ff.CollectionFF
    ]

    def __init__(self, request):
        self.request = request.GET.copy()
        self.facet_filter_types = [
            ff_field(request) for ff_field in self.facet_filter_fields
        ]

        for field in self.simple_fields:
            if isinstance(self.simple_fields[field], list):
                self.__dict__.update({
                    field: request.GET.getlist(field)
                })
            else:
                self.__dict__.update({
                    field: request.GET.get(field, self.simple_fields[field])
                })

        self.sort = self.sort_field(request).sort

    def context(self):
        fft = [{
            'form_name': f.form_name,
            'facet': f.es_facet_field,
            'display_name': f.display_name,
            'filter': f.es_filter_field,
            'faceting_allowed': f.faceting_allowed
        } for f in self.facet_filter_types]

        search_form = {
            'q': self.q,
            'rq': self.rq,
            'rows': self.rows,
            'start': self.start,
            'sort': self.sort,
            'view_format': self.view_format,
            'rc_page': self.rc_page,
            'facet_filter_types': fft
        }
        return search_form

    def es_encode(self, facet_types=[]):
        terms = (
            [solr_escape(self.q)] +
            [solr_escape(q) for q in self.rq] +
            self.request.getlist('fq')
        )
        terms = [q for q in terms if q]
        self.query_string = (
            terms[0] if len(terms) == 1 else " AND ".join(terms))

        es_query_string = {
            "must": [{
                "query_string": {
                    "query": self.query_string
                }
            }]
        }

        es_query_filters = {
            "filter": [ft.es_query for ft in self.facet_filter_types
                       if ft.es_query]
        }

        try:
            rows = int(self.rows)
            start = int(self.start)
        except ValueError as err:
            raise Http404("{0} does not exist".format(err))

        sort = constants.SORT_OPTIONS[self.sort]
        print(f'TODO: set sort for ES: {sort}')

        if len(facet_types) == 0:
            facet_types = self.facet_filter_types

        aggs = {}
        for facet_type in facet_types:
            aggs.update({
                facet_type.es_facet_field: {
                    "terms": {
                        "field": facet_type.es_facet_field
                    }
                }
            })

        if self.query_string:
            es_query_filters.update(es_query_string)

        es_query = {
            "query": {
                "bool": es_query_filters
            },
            "size": rows,
            "from": start,
            "aggs": aggs
        }
        # TODO: add sort!

        # query_fields = self.request.get('qf')
        # if query_fields:
        #     solr_query.update({'qf': query_fields})

        return es_query

    def get_facets(self, extra_filter=None):
        # get facet counts
        # if the user's selected some of the available facets (ie - there are
        # filters selected for this field type) perform a search as if those
        # filters were not applied to obtain facet counts
        #
        # since we AND filters of the same type, counts should go UP when
        # more than one facet is selected as a filter, not DOWN (or'ed filters
        # of the same type)

        facets = {}
        for fft in self.facet_filter_types:
            if (len(fft.es_query) > 0):
                exclude_filter = fft.es_query
                fft.es_query = None
                es_params = self.es_encode([fft])
                fft.es_query = exclude_filter

                if extra_filter:
                    (es_params.get('query')
                        .get('bool')
                        .get('filter')
                        .append({
                            "terms": extra_filter
                        }))

                facet_search = elastic_client.search(
                    index="calisphere-items", body=es_params)

                # make it look like solr
                buckets = (
                    facet_search
                    .get('aggregations')
                    .get(fft.es_facet_field)
                    .get('buckets')
                )
                self.es_facets[fft.es_facet_field] = {
                    b['key']: b['doc_count'] for b in buckets}

            es_facets = self.es_facets[fft.es_facet_field]

            facets[fft.es_facet_field] = fft.es_process_facets(es_facets)

            for j, facet_item in enumerate(facets[fft.es_facet_field]):
                facets[fft.es_facet_field][j] = (fft.es_facet_transform(
                    facet_item[0]), facet_item[1])

        return facets

    def search(self, extra_filter=None):
        es_query = self.es_encode()

        if extra_filter:
            (es_query.get('query')
                .get('bool')
                .get('filter')
                .append({
                    "terms": extra_filter
                }))

        results = elastic_client.search(
            index="calisphere-items", body=es_query)

        aggs = results.get('aggregations')
        facet_counts = {'facet_fields': {}}
        for facet_field in aggs:
            buckets = aggs[facet_field].get('buckets')
            facet_values = {b['key']: b['doc_count'] for b in buckets}
            facet_counts['facet_fields'][facet_field] = facet_values

        es_results = ESResults(
            results['hits']['hits'],
            results['hits']['total']['value'],
            facet_counts)

        self.es_facets = facet_counts['facet_fields']
        return es_results

    def filter_display(self):
        filter_display = {}
        for filter_type in self.facet_filter_types:
            param_name = filter_type['form_name']
            display_name = filter_type['es_filter_field']
            filter_transform = filter_type['filter_display']

            if len(self.request.getlist(param_name)) > 0:
                filter_display[display_name] = list(
                    map(filter_transform, self.request.getlist(param_name)))
        return filter_display


class CampusForm(SearchForm):
    def __init__(self, request, campus):
        super().__init__(request)
        self.institution = campus

    def es_encode(self, facet_types=[]):
        es_query = super().es_encode(facet_types)
        (es_query.get('query')
            .get('bool')
            .get('filter')
            .append({
                "terms": self.institution.es_filter
            }))
        return es_query


class RepositoryForm(SearchForm):
    facet_filter_fields = [
        ff.TypeFF,
        ff.DecadeFF,
        ff.CollectionFF
    ]

    def __init__(self, request, institution):
        super().__init__(request)
        self.institution = institution

    def es_encode(self, facet_types=[]):
        es_query = super().es_encode(facet_types)
        (es_query.get('query')
            .get('bool')
            .get('filter')
            .append({
                "terms": self.institution.es_filter
            }))
        return es_query


class CollectionForm(SearchForm):
    facet_filter_fields = [
        ff.TypeFF,
        ff.DecadeFF,
    ]

    def __init__(self, request, collection):
        super().__init__(request)
        self.collection = collection
        facet_filter_types = self.facet_filter_types
        facet_filter_types += collection.custom_facets
        # If relation_ss is not already defined as a custom facet, and is
        # included in search parameters, add the relation_ss facet implicitly
        # this is a bit crude and assumes if any custom facets, relation_ss 
        # is a custom facet
        if not collection.custom_facets:
            if request.GET.get('relation_ss'):
                facet_filter_types.append(ff.RelationFF(request))
        self.facet_filter_types = facet_filter_types

    def es_encode(self, facet_types=[]):
        es_query = super().es_encode(facet_types)
        (es_query.get('query')
            .get('bool')
            .get('filter')
            .append({
                "terms": self.collection.es_filter
            }))
        return es_query


class AltSortField(SortField):
    default = 'oldest-end'
    no_keyword = 'oldest-end'


class CollectionFacetValueForm(CollectionForm):
    simple_fields = {
        'q': '',
        'rq': [],
        'rows': 48,
        'start': 0,
        'view_format': 'list',
        'rc_page': 0
    }
    sort_field = AltSortField
