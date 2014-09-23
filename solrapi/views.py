from django.shortcuts import render
from django.http import HttpResponse
from django import forms
from django.conf import settings

import md5s3stash
import operator
import math
import solr
import re
import urllib2
import simplejson as json

FACET_TYPES = [('type', 'Type of Object'), ('repository_name', 'Institution Owner'), ('collection_name', 'Collection')]
SOLR = solr.Solr('http://107.21.228.130:8080/solr/dc-collection')


def md5_to_http_url(md5):
    return md5s3stash.md5_to_http_url(md5, 'ucldc')

def process_media(item):
    if 'reference_image_md5' in item:
        item['reference_image_http'] = md5_to_http_url(item['reference_image_md5'])

# concat query with 'AND'
def concat_query(q, rq):
    if q == '':
        return rq
    elif rq == '':
        return q
    else:
        return q + ' AND ' + rq

# concat filters with 'OR'
def concat_filters(filters, filter_type):
    # OR-ING FILTERS OF ONE TYPE, YET AND-ING FILTERS OF DIFF TYPES
    fq_contents = filter_type + ': '
    
    for counter, f in enumerate(filters):
        fq_contents = fq_contents + '"' + f + '"'
        # if not at the last filter term, continue OR-ing together terms
        if counter < len(filters)-1:
            fq_contents = fq_contents + " OR " + filter_type + ': '
    
    return [fq_contents]

# collect filters into an array
def solrize_filters(filters):
    fq = []
    for filter_type in FACET_TYPES:
        if len(filters[filter_type[0]]) > 0:
            fq.extend(concat_filters(filters[filter_type[0]], filter_type[0]))
    
    return fq


def process_facets(facets, filters, facet_counts=None):
    display_facets = {}
    
    # if we're displaying facets with a current count of 0, change their counts to reflect current count
    # if facet_counts:
    #     for facet, count in facets.iteritems():
    #         if count != 0:
    #             display_facets[facet] = facet_counts[facet]
    # else: 
    display_facets = dict((facet, count) for facet, count in facets.iteritems() if count != 0)
    
    display_facets = sorted(display_facets.iteritems(), key=operator.itemgetter(1), reverse=True)
    for f in filters:
        if not any(f in facet for facet in display_facets):
            display_facets.append((f, 0))
            
    return display_facets



def search(request):
    if request.method == 'GET':
        # concatenate query terms from refine query and query box
        q = reduce(concat_query, request.GET.getlist('q'))
        # set rows to 16 by default, unless there is a different number specified
        rows = request.GET['rows'] if 'rows' in request.GET else '16'
        # set start to 0 by default, unless there is a different page specified
        start = request.GET['start'] if 'start' in request.GET else '0'
        # set view format to thumbnails by default, unless list is specified
        view_format = request.GET['view_format'] if 'view_format' in request.GET else 'thumbnails'
        
        # for each filter_type tuple ('solr_name', 'Display Name') in the list FACET_TYPES
        # create a dictionary with key solr_name of filter and value list of parameters for that filter
        filters = dict((filter_type[0], request.GET.getlist(filter_type[0])) for filter_type in FACET_TYPES)
        
        fq = solrize_filters(filters)
        
        # perform the search
        solr_search = SOLR.select(
            q=q,
            rows=rows,
            start=start,
            fq=fq,
            facet='true', 
            facet_limit='-1',
            facet_field=list(facet_type[0] for facet_type in FACET_TYPES)
        )
        
        for item in solr_search.results:
            process_media(item)
        
        facets = {}
        for facet_type in FACET_TYPES:
            if len(filters[facet_type[0]]) > 0:
                # tmp_solr_search = SOLR.select(
                #     q=q,
                #     rows=rows,
                #     start=start,
                #     facet='true',
                #     facet_limit='-1',
                #     facet_field=list(facet_type[0] for facet_type in FACET_TYPES)
                # )
                
                # All the filters except the ones of the current filter type
                tmp_filters = {key: value for key, value in filters.items()
                    if key != facet_type[0]}
                tmp_filters[facet_type[0]] = []
                
                tmp_fq = solrize_filters(tmp_filters)
                tmp_solr_search = SOLR.select(
                    q=q,
                    rows=rows,
                    start=start,
                    fq=tmp_fq,
                    facet='true',
                    facet_limit='-1',
                    facet_field=list(facet_type[0] for facet_type in FACET_TYPES)
                )
                
                
                facets[facet_type[0]] = process_facets(
                    tmp_solr_search.facet_counts['facet_fields'][facet_type[0]],
                    filters[facet_type[0]],
                    solr_search.facet_counts['facet_fields'][facet_type[0]]
                )
            else: 
                facets[facet_type[0]] = process_facets(
                    solr_search.facet_counts['facet_fields'][facet_type[0]], 
                    filters[facet_type[0]]
                )
        
        return render(request, 'public_interface/searchResults.html', {
            'q': q,
            'filters': filters,
            'rows': rows,
            'start': start,
            'search_results': solr_search.results,
            'facets': facets,
            'FACET_TYPES': FACET_TYPES,
            'numFound': solr_search.numFound,
            'pages': int(math.ceil(float(solr_search.numFound)/int(rows))),
            'view_format': view_format
        })
        
    return render (request, 'public_interface/base.html', {'q': ''})

def home(request):
    return render(request, 'public_interface/base.html', {'q': ''})

def itemView(request, item_id=''):
    item_id = 'id:' + "\"" + item_id + "\""
    
    if request.method == 'POST' and 'q' in request.POST:
        q = request.POST['q']
        rows = 6
        start = request.POST['start'] if 'start' in request.POST else '0'
        
        filters = dict((filter_type[0], request.GET.getlist(filter_type[0])) for filter_type in FACET_TYPES)
        fq = solrize_filters(filters)
        
        solr_search = SOLR.select(
            q=q,
            rows='6',
            start=start,
            fq=fq
        )
        
        for item in solr_search.results:
            process_media(item)
        
        carousel_items = solr_search.results
        numFound = solr_search.numFound
    else:
        # MORE LIKE THIS RESULTS
        q = ''
        carousel_items = {}
        numFound = 0
    
    solr_item = SOLR.select(q=item_id)
    for item in solr_item.results:
        process_media(item)
    
    context = {'q': q, 'docs': solr_item.results, 'carousel': carousel_items, 'numFound': numFound}
    
    return render(request, 'public_interface/item.html', context)

def collectionsExplore(request):
    s = solr.Solr('http://107.21.228.130:8080/solr/dc-collection')
    
    collections_solr_query = SOLR.select(q='*:*', rows=0, start=0, facet='true', facet_field=['collection'], facet_limit='10')
    solr_collections = collections_solr_query.facet_counts['facet_fields']['collection']
    
    collections = []
    for collection_url in solr_collections:
        collection_api = urllib2.urlopen(collection_url + "?format=json")
        collection_json = collection_api.read()
        collection_details = json.loads(collection_json)
        rows = '4' if collection_details['description'] != '' else '5'
        display_items = SOLR.select(
            q='*:*', 
            fields='reference_image_md5, title, id', 
            rows=rows, 
            start=0, 
            fq=['collection: \"' + collection_url + '\"']
        )
        
        for item in display_items:
            if 'reference_image_md5' in item:
                item['reference_image_http'] = md5_to_http_url(item['reference_image_md5'])
        
        collection_url_pattern = re.compile('https://registry.cdlib.org/api/v1/collection/([0-9]+)[/]?')
        collection_id = collection_url_pattern.match(collection_url)
        
        collections.append({
            'name': collection_details['name'], 
            'description': collection_details['description'], 
            'slug': collection_details['slug'],
            'collection_id': collection_id.group(1),
            'display_items': display_items.results
        })
    
    return render(request, 'public_interface/collections-explore.html', {'collections': collections})

def collectionView(request, collection_id):
    if request.method == 'GET':
        q = reduce(concat_query, request.GET.getlist('q')) if 'q' in request.GET else '*:*'
        rows = request.GET['rows'] if 'rows' in request.GET else '16'
        start = request.GET['start'] if 'start' in request.GET else '0'
        view_format = request.GET['view_format'] if 'view_format' in request.GET else 'thumbnails'
        
        collection_url = 'https://registry.cdlib.org/api/v1/collection/' + collection_id + '/?format=json'
        collection_json = urllib2.urlopen(collection_url).read()
        collection_details = json.loads(collection_json)
        
        filters = dict((filter_type[0], request.GET.getlist(filter_type[0])) for filter_type in FACET_TYPES)
        filters['collection_name'] = [collection_details['name']]
        fq = solrize_filters(filters)
        
        # perform the search
        s = solr.Solr('http://107.21.228.130:8080/solr/dc-collection')
        solr_response = SOLR.select(
            q=q,
            rows=rows,
            start=start,
            fq=fq,
            facet='true', 
            facet_field=list(facet_type[0] for facet_type in FACET_TYPES)
        )
        
        for item in solr_response.results:
            if 'reference_image_md5' in item:
                item['reference_image_http'] = md5_to_http_url(item['reference_image_md5'])
        
        facets = {}
        for facet_type in FACET_TYPES:
            facets[facet_type[0]] = process_facets(
                solr_response.facet_counts['facet_fields'][facet_type[0]], 
                filters[facet_type[0]]
            )
        
        return render(request, 'public_interface/collectionResults.html', {
            'q': q,
            'filters': filters,
            'rows': rows,
            'start': start,
            'search_results': solr_response.results,
            'facets': facets,
            'FACET_TYPES': FACET_TYPES,
            'numFound': solr_response.numFound,
            'pages': int(math.ceil(float(solr_response.numFound)/int(rows))),
            'view_format': view_format, 
            'collection': collection_details
        })
    
    return render(request, 'public_interface/searchResults.html', {'yay': 'yamy'})
