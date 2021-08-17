from .cache_retry import SOLR_select
from . import constants
from django.http import Http404
from . import facet_filter_type as ff


def solr_escape(text):
    return text.replace('?', '\\?').replace('"', '\\"')


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
            'facet': f.solr_facet_field,
            'display_name': f.display_name,
            'filter': f.solr_filter_field,
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

    def solr_encode(self, facet_types=[]):
        # concatenate query terms from refine query and query box
        terms = (
            [solr_escape(self.q)] +
            [solr_escape(q) for q in self.rq] +
            self.request.getlist('fq')
        )
        terms = [q for q in terms if q]
        qt_string = terms[0] if len(terms) == 1 else " AND ".join(terms)
        # qt_string = qt_string.replace('?', '')

        filters = [ft.solr_query for ft in self.facet_filter_types
                   if ft.solr_query]

        try:
            rows = int(self.rows)
            start = int(self.start)
        except ValueError as err:
            raise Http404("{0} does not exist".format(err))

        sort = constants.SORT_OPTIONS[self.sort]

        if len(facet_types) == 0:
            facet_types = self.facet_filter_types

        solr_query = {
            'q': qt_string,
            'rows': rows,
            'start': start,
            'sort': sort,
            'fq': filters,
            'facet': 'true',
            'facet_mincount': 1,
            'facet_limit': '-1',
            'facet_field':
            list(facet_type['solr_facet_field'] for facet_type in facet_types)
        }

        query_fields = self.request.get('qf')
        if query_fields:
            solr_query.update({'qf': query_fields})

        return solr_query

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
            if (len(fft.solr_query) > 0):
                exclude_filter = fft.solr_query
                fft.solr_query = None
                solr_params = self.solr_encode([fft])
                fft.solr_query = exclude_filter

                if extra_filter:
                    solr_params['fq'].append(extra_filter)
                facet_search = SOLR_select(**solr_params)

                self.facets[fft.solr_facet_field] = (
                    facet_search.facet_counts['facet_fields']
                    [fft.solr_facet_field])

            solr_facets = self.facets[fft.solr_facet_field]

            facets[fft.form_name] = fft.process_facets(solr_facets)

            for j, facet_item in enumerate(facets[fft.form_name]):
                facets[fft.form_name][j] = (fft.facet_transform(
                    facet_item[0]), facet_item[1])

        return facets

    def search(self, extra_filter=None):
        solr_query = self.solr_encode()
        if extra_filter:
            solr_query['fq'].append(extra_filter)
        results = SOLR_select(**solr_query)
        self.facets = results.facet_counts['facet_fields']
        return results

    def filter_display(self):
        filter_display = {}
        for filter_type in self.facet_filter_types:
            param_name = filter_type['solr_facet_field']
            display_name = filter_type['solr_filter_field']
            filter_transform = filter_type['filter_display']

            if len(self.request.getlist(param_name)) > 0:
                filter_display[display_name] = list(
                    map(filter_transform, self.request.getlist(param_name)))
        return filter_display


class CampusForm(SearchForm):
    def __init__(self, request, campus):
        super().__init__(request)
        self.institution = campus

    def solr_encode(self, facet_types=[]):
        solr_query = super().solr_encode(facet_types)
        solr_query['fq'].append(self.institution.solr_filter)
        return solr_query


class RepositoryForm(SearchForm):
    facet_filter_fields = [
        ff.TypeFF,
        ff.DecadeFF,
        ff.CollectionFF
    ]
    def __init__(self, request, institution):
        super().__init__(request)
        self.institution = institution

    def solr_encode(self, facet_types=[]):
        solr_query = super().solr_encode(facet_types)
        solr_query['fq'].append(self.institution.solr_filter)
        return solr_query


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

    def solr_encode(self, facet_types=[]):
        solr_query = super().solr_encode(facet_types)
        solr_query['fq'].append(self.collection.solr_filter)
        return solr_query


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
