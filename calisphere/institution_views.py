from future import standard_library
from django.shortcuts import render
from django.urls import reverse
from django.http import Http404
from . import constants
from .cache_retry import SOLR_select, json_loads_url
from .search_form import CampusForm, RepositoryForm
from .collection_views import Collection, get_rc_from_ids
from .facet_filter_type import (
    CollectionFF, RepositoryFF)
from django.apps import apps
from django.conf import settings


import math
import re
import string

standard_library.install_aliases()

repo_regex = (r'https://registry\.cdlib\.org/api/v1/repository/'
              r'(?P<repository_id>\d*)/?')
repo_template = "https://registry.cdlib.org/api/v1/repository/{0}/"
campus_template = "https://registry.cdlib.org/api/v1/campus/{0}/"

col_regex = (r'https://registry\.cdlib\.org/api/v1/collection/'
             r'(?P<id>\d*)/?')


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


def campus_directory(request):
    repositories_query = SOLR_select(
        q='*:*',
        rows=0,
        start=0,
        facet='true',
        facet_mincount=1,
        facet_field=['repository_url'],
        facet_limit='-1')
    index_repositories = repositories_query.facet_counts['facet_fields'][
        'repository_url']

    repositories = []
    for repository_url in index_repositories:
        repo_id = re.match(repo_regex, repository_url).group('repository_id')
        repository = Repository(repo_id).get_repo_data()
        if repository['campus']:
            repositories.append({
                'name': repository['name'],
                'campus': repository['campus'],
                'repository_id': repo_id
            })

    repositories = sorted(
        repositories,
        key=lambda repository: (repository['campus'], repository['name']))
    # Use hard-coded campus list so UCLA ends up in the correct order
    # campuses = sorted(list(set(
    #     [repository['campus'] for repository in repositories])))

    return render(
        request, 'calisphere/campusDirectory.html', {
            'repositories': repositories,
            'campuses': constants.CAMPUS_LIST,
            'state_repositories': None,
            'description': None,
        })


def statewide_directory(request):
    repositories_query = SOLR_select(
        q='*:*',
        rows=0,
        start=0,
        facet='true',
        facet_mincount=1,
        facet_field=['repository_url'],
        facet_limit='-1')
    index_repositories = repositories_query.facet_counts['facet_fields'][
        'repository_url']
    repositories = []
    for repository_url in index_repositories:
        repo_id = re.match(repo_regex, repository_url).group('repository_id')
        repository = Repository(repo_id).get_repo_data()
        if repository['campus'] == '':
            repositories.append({
                'name':
                repository['name'],
                'repository_id':
                re.match(
                    repo_regex,
                    repository['url']).group('repository_id')
            })

    binned_repositories = []
    bin = []
    for repository in repositories:
        if repository['name'][0] in string.punctuation:
            bin.append(repository)
    if len(bin) > 0:
        binned_repositories.append({'punctuation': bin})

    for char in string.ascii_uppercase:
        bin = []
        for repository in repositories:
            if repository['name'][0] == char or repository['name'][
                    0] == char.upper:
                bin.append(repository)
        if len(bin) > 0:
            bin.sort(key=lambda r: r['name'])
            binned_repositories.append({char: bin})

    return render(
        request, 'calisphere/statewideDirectory.html', {
            'state_repositories': binned_repositories,
            'campuses': None,
            'meta_image': None,
            'description': None,
            'q': None,
        })


class Campus(object):
    def __init__(self, slug):
        campus = [c for c in constants.CAMPUS_LIST if slug == c['slug']][0]
        if not campus:
            raise Http404(f"{slug} campus does not exist.")

        self.slug = slug
        self.id = campus.get('id')
        self.featured_image = campus.get('featuredImage')
        self.url = campus_template.format(self.id)

        self.details = json_loads_url(self.url + "?format=json")
        if not self.details:
            raise Http404("{0} does not exist".format(self.id))

        self.name = self.full_name = self.details.get('name')
        if self.details.get('ark'):
            self.contact_info = json_loads_url(
                "http://dsc.cdlib.org/institution-json/" +
                self.details.get('ark'))
        else:
            self.contact_info = ''

        self.filter = 'campus_url: "' + self.url + '"'


class Repository(object):
    def __init__(self, id):
        self.id = id
        self.url = repo_template.format(id)

        app = apps.get_app_config('calisphere')
        self.details = app.registry.repository_data.get(
            int(self.id), None)

        if not self.details:
            self.details = json_loads_url(self.url + "?format=json")

        if not self.details:
            raise Http404("{0} does not exist".format(id))

        self.name = self.full_name = self.details.get('name')
        if self.details.get('campus'):
            self.full_name = (
                f"{self.details.get('campus')[0]['name']} / {self.name}")
            self.campus = self.details.get('campus')[0]['name']

        self.featured_image = None
        if not self.details.get('campus'):
            feat = [u for u in constants.FEATURED_UNITS
                    if u['id'] == self.id]
            if feat:
                self.featured_image = feat[0].get('featuredImage')

        self.filter = 'repository_url: "' + self.url + '"'

    def __str__(self):
        return f"{self.id}: {self.details.name}"

    def get_repo_data(self):
        repository = {
            'id': self.id,
            'url': self.url,
            'name': self.details['name'],
        }

        if self.details['campus']:
            repository['campus'] = self.details['campus'][0]['name']
        else:
            repository['campus'] = ''

        repository['ga_code'] = self.details.get(
            'google_analytics_tracking_code', None)

        production_aeon = settings.UCLDC_FRONT == 'https://calisphere.org/'
        if production_aeon:
            repository['aeon_url'] = self.details.get('aeon_prod', None)
        else:
            repository['aeon_url'] = self.details.get('aeon_test', None)

        parent = self.details['campus']
        pslug = ''
        if len(parent):
            pslug = '{0}-'.format(parent[0].get('slug', None))
        repository['slug'] = pslug + self.details.get('slug', None)
        return repository

    def get_contact_info(self):
        if hasattr(self, 'contact_info'):
            return self.contact_info

        self.contact_info = ''
        if self.details.get('ark'):
            self.contact_info = json_loads_url(
                "http://dsc.cdlib.org/institution-json/" +
                self.details.get('ark'))
        return self.contact_info


def institution_search(request, form, institution):
    results = form.search()
    facets = form.get_facets(institution.filter)
    filter_display = form.filter_display()

    page = (int(form.start) // int(form.rows)) + 1
    title = f"{institution.full_name} Items"
    if (page > 1):
        title = (f"{institution.full_name} Items - page {page}")

    rc_ids = [cd[0]['id'] for cd in facets['collection_data']]
    if len(request.GET.getlist('collection_data')):
        rc_ids = request.GET.getlist('collection_data')

    num_related_collections = len(rc_ids)
    rcs = get_rc_from_ids(
        rc_ids, form.rc_page, form.query_string)

    context = {
        'title': title,
        'search_form': form.context(),
        'q': form.q,
        'filters': filter_display,
        'search_results': results.results,
        'facets': facets,
        'numFound': results.numFound,
        'pages': int(math.ceil(
            results.numFound / int(form.rows))),
        'num_related_collections': num_related_collections,
        'related_collections': rcs
    }

    return context


def institution_collections(request, institution):

    page = int(request.GET['page']) if 'page' in request.GET else 1

    collections_params = {
        'q': '',
        'rows': 0,
        'start': 0,
        'fq': [institution.filter],
        'facet': 'true',
        'facet_mincount': 1,
        'facet_limit': '-1',
        'facet_field': ['sort_collection_data'],
        'facet_sort': 'index'
    }

    collections_search = SOLR_select(**collections_params)
    sort_collection_data = collections_search.facet_counts['facet_fields'][
        'sort_collection_data']

    pages = int(math.ceil(len(sort_collection_data) / 10))

    # solrpy gives us a dict == unsorted (!)
    # use the `facet_decade` mode of process_facets to do a
    # lexical sort by value ....
    col_fft = CollectionFF(request)
    related_collections = list(
        collection[0] for collection in
        col_fft.process_facets(sort_collection_data, 'value'))
    start = ((page-1) * 10)
    end = page * 10
    related_collections = related_collections[start:end]

    related_collections = []
    for i, related_collection in enumerate(related_collections):
        collection_parts = process_sort_collection_data(
            related_collection)
        col_id = re.match(col_regex, collection_parts[2]).group('id')
        try:
            related_collections.append(
                Collection(col_id).get_mosaic())
        except Http404:
            pass

    context = {
        'page': page,
        'pages': pages,
        'collections': related_collections,
    }

    if page + 1 <= pages:
        context['next_page'] = page + 1
    if page - 1 > 0:
        context['prev_page'] = page - 1

    return context


def repository_search(request, repository_id):
    institution = Repository(repository_id)
    form = RepositoryForm(request, institution)

    context = institution_search(request, form, institution)

    context.update({
        'institution': institution.details,
        'contact_information': institution.get_contact_info(),
        'repository_id': institution.id,
        'uc_institution': institution.details.get('campus', False),
        'form_action': reverse(
            'calisphere:repositorySearch',
            kwargs={'repository_id': institution.id}
        ),
        'featuredImage': institution.featured_image
    })

    return render(request, 'calisphere/institutionViewItems.html', context)


def repository_collections(request, repository_id):
    institution = Repository(repository_id)

    context = institution_collections(request, institution)

    context.update({
        'contact_information': institution.get_contact_info(),
        'institution': institution.details,
        'repository_id': institution.id,
        'uc_institution': institution.details.get('campus', False),
        'featuredImage': institution.featured_image
    })

    # title for UC institutions needs to show parent campus
    # refactor, as this is copy/pasted in this commit
    context['title'] = institution.full_name
    if context['page'] > 1:
        context['title'] = (
            f"{institution.full_name} Collections - page {context['page']}")

    return render(request, 'calisphere/institutionViewCollections.html',
                  context)


def campus_search(request, campus_slug):
    institution = Campus(campus_slug)
    form = CampusForm(request, institution)
    context = institution_search(request, form, institution)

    context.update({
        'institution': institution.details,
        'contact_information': institution.contact_info,
        'repository_id': None,
        'campus_slug': institution.slug,
        'form_action': reverse(
            'calisphere:campusSearch',
            kwargs={'campus_slug': institution.slug}),
        'featuredImage': institution.featured_image
    })

    return render(request, 'calisphere/institutionViewItems.html', context)


def campus_collections(request, campus_slug):
    institution = Campus(campus_slug)

    context = institution_collections(request, institution)
    context['title'] = institution.name
    if context['page'] > 1:
        context['title'] = (
            f"{institution.name} Collections - page {context['page']}")

    context.update({
        'contact_information': institution.contact_info,
        'institution': institution.details,
        'campus_slug': institution.slug,
        'featuredImage': institution.featured_image,
        'repository_id': None,
    })
    context['institution']['campus'] = None

    return render(request, 'calisphere/institutionViewCollections.html',
                  context)


def campus_institutions(request, campus_slug):
    institution = Campus(campus_slug)

    institutions_search = SOLR_select(
        q='',
        rows=0,
        start=0,
        fq=['campus_url: "' + institution.url + '"'],
        facet='true',
        facet_mincount=1,
        facet_limit='-1',
        facet_field=['repository_data'])
    institutions = institutions_search.facet_counts['facet_fields'][
        'repository_data']

    repo_fft = RepositoryFF(request)

    related_institutions = list(
        institution[0] for institution in
        repo_fft.process_facets(institutions))

    for i, related_institution in enumerate(related_institutions):
        repo_url = related_institution.split('::')[0]
        repo_id = re.match(repo_regex, repo_url).group('repository_id')
        related_institutions[i] = Repository(repo_id).get_repo_data()
    related_institutions = sorted(
        related_institutions,
        key=lambda related_institution: related_institution['name'])

    return render(
        request,
        'calisphere/institutionViewInstitutions.html',
        {
            # 'campus': institution.name,
            'title': f'{institution.name} Contributors',
            'featuredImage': institution.featured_image,
            'campus_slug': campus_slug,
            'institutions': related_institutions,
            'institution': institution.details,
            'contact_information': institution.contact_info,
            'repository_id': None,
        })
