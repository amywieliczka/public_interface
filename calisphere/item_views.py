import urllib.parse
import re

from django.http import Http404, QueryDict
from django.conf import settings
from django.shortcuts import render, redirect

from .cache_retry import SOLR_select, SOLR_raw, json_loads_url
from .facet_filter_type import getCollectionData, getRepositoryData
from .views import getRelatedCollections, itemViewCarouselMLT
from .constants import *
from .collection_views import Collection

registry_url = "https://registry.cdlib.org/api/v1/collection/(?P<col_id>\d+)/"

def parse_col_id(col_url):
    return col_url.split(
        'https://registry.cdlib.org/api/v1/collection/', 1)[1][:-1]

def getMoreCollectionData(collection_data):
    collection = getCollectionData(
        collection_data=collection_data,
        collection_id=None,
    )
    collection_details = json_loads_url("{0}?format=json".format(
        collection['url']))
    if not collection_details:
        return None

    collection['local_id'] = collection_details['local_id']
    collection['slug'] = collection_details['slug']
    collection['harvest_type'] = collection_details['harvest_type']
    collection['custom_facet'] = collection_details['custom_facet']

    production_disqus = settings.UCLDC_FRONT == 'https://calisphere.org/' or settings.UCLDC_DISQUS == 'prod'
    if production_disqus:
        collection['disqus_shortname'] = collection_details.get(
            'disqus_shortname_prod')
    else:
        collection['disqus_shortname'] = collection_details.get(
            'disqus_shortname_test')

    return collection

def getHostedContentFile(structmap):
    contentFile = ''
    if structmap['format'] == 'image':
        iiif_url = '{}{}/info.json'.format(settings.UCLDC_IIIF,
                                                structmap['id'])
        if iiif_url.startswith('//'):
            iiif_url = ''.join(['http:', iiif_url])
        iiif_info = json_loads_url(iiif_url)
        if not iiif_info:
            return None
        size = iiif_info.get('sizes', [])[-1]
        if size['height'] > size['width']:
            access_size = {
                'width': ((size['width'] * 1024) // size['height']),
                'height': 1024
            }
            access_url = iiif_info['@id'] + "/full/,1024/0/default.jpg"
        else:
            access_size = {
                'width': 1024,
                'height': ((size['height'] * 1024) // size['width'])
            }
            access_url = iiif_info['@id'] + "/full/1024,/0/default.jpg"

        contentFile = {
            'titleSources': iiif_info,
            'format': 'image',
            'size': access_size,
            'url': access_url
        }
    if structmap['format'] == 'file':
        contentFile = {
            'id': structmap['id'],
            'format': 'file',
        }
    if structmap['format'] == 'video':
        access_url = os.path.join(settings.UCLDC_MEDIA, structmap['id'])
        contentFile = {
            'id': structmap['id'],
            'format': 'video',
            'url': access_url
        }
    if structmap['format'] == 'audio':
        access_url = os.path.join(settings.UCLDC_MEDIA, structmap['id'])
        contentFile = {
            'id': structmap['id'],
            'format': 'audio',
            'url': access_url
        }

    return contentFile

METADATA_DISPLAY = [
    {"label": "Title", "field": "title", "itemProp": "name"},
    {"label": "Alternative Title", "field": "alternative_title", "itemProp": None},
    {"label": "Creator", "field": "creator", "itemProp": "creator"},
    {"label": "Contributor", "field": "contributor", "itemProp": "contributor"},
    {"label": "Date Created and/or Issued", "field": "date", "itemProp": "dateCreated"},
    {"label": "Publication Information", "field": "publisher", "itemProp": None},
    {"label": "Rights Information", "field": ["rights", "rights_uri"], "itemProp": None},
    {"label": "Rights Holder and Contact", "field": "rights_holder", "itemProp": "copyrightHolder"},
    {"label": "Rights Notes", "field": "rights_note", "itemProp": None},
    {"label": "Date of Copyright", "field": "rights_date", "itemProp": "copyrightYear"},
    {"label": "Description", "field": "description", "itemProp": "description"},
    {"label": "Type", "field": "type", "itemProp": None},
    {"label": "Format", "field": "format", "itemProp": None},
    {"label": "Form/Genre", "field": "genre", "itemProp": "genre"},
    {"label": "Extent", "field": "extent", "itemProp": None},
    {"label": "Identifier", "field": "identifier", "itemProp": None},
    {"label": "Language", "field": "language", "itemProp": "inLanguage"},
    {"label": "Subject", "field": "subject", "itemProp": "about"},
    {"label": "Time Period", "field": "temporal", "itemProp": None},
    {"label": "Place", "field": "coverage", "itemProp": None},
    {"label": "Source", "field": "source", "itemProp": None},
    {"label": "Relation", "field": "relation", "itemProp": None},
    {"label": "Provenance", "field": "provenance", "itemProp": None},
    {"label": "Location", "field": "location", "itemProp": None},
    {"label": "Transcription", "field": "transcription", "itemProp": None}
]

def itemView(request, item_id=''):
    item_id_search_term = 'id:"{0}"'.format(item_id)
    item_solr_search = SOLR_select(q=item_id_search_term)
    if not item_solr_search.numFound:
        # second level search
        def _fixid(id):
            return re.sub(r'^(\d*--http:/)(?!/)', r'\1/', id)

        old_id_search = SOLR_select(
            q='harvest_id_s:*{}'.format(_fixid(item_id)))
        if old_id_search.numFound:
            return redirect('calisphere:itemView',
                            old_id_search.results[0]['id'])
        else:
            raise Http404("{0} does not exist".format(item_id))

    item = item_solr_search.results[0]
    if 'reference_image_dimensions' in item:
        item['reference_image_dimensions'] = item['reference_image_dimensions'].split(':')
    if 'structmap_url' in item and len(item['structmap_url']) >= 1:
        item['harvest_type'] = 'hosted'
        structmap_url = item['structmap_url'].replace(
            's3://static', 'https://s3.amazonaws.com/static')
        structmap_data = json_loads_url(structmap_url)

        if 'structMap' in structmap_data:
            # complex object
            if 'order' in request.GET and 'structMap' in structmap_data:
                # fetch component object
                item['selected'] = False
                order = int(request.GET['order'])
                item['selectedComponentIndex'] = order
                component = structmap_data['structMap'][order]
                component['selected'] = True
                if 'format' in component:
                    item['contentFile'] = getHostedContentFile(component)
                # remove emptry strings from list
                for k, v in list(component.items()):
                    if isinstance(v, list):
                        if isinstance(v[0], str):
                            component[k] = [
                                name for name in v if name and name.strip()
                            ]
                # remove empty lists and empty strings from dict
                item['selectedComponent'] = dict(
                    (k, v) for k, v in list(component.items()) if v)
            else:
                item['selected'] = True
                # if parent content file, get it
                if 'format' in structmap_data:
                    item['contentFile'] = getHostedContentFile(
                        structmap_data)
                # otherwise get first component file
                else:
                    component = structmap_data['structMap'][0]
                    item['contentFile'] = getHostedContentFile(component)
            item['structMap'] = structmap_data['structMap']

            # single or multi-format object
            formats = [
                component['format']
                for component in structmap_data['structMap']
                if 'format' in component
            ]
            if len(set(formats)) > 1:
                item['multiFormat'] = True
            else:
                item['multiFormat'] = False

            # carousel has captions or not
            if all(f == 'image' for f in formats):
                item['hasComponentCaptions'] = False
            else:
                item['hasComponentCaptions'] = True

            # number of components
            item['componentCount'] = len(structmap_data['structMap'])

            # has fixed item thumbnail image
            if 'reference_image_md5' in item:
                item['has_fixed_thumb'] = True
            else:
                item['has_fixed_thumb'] = False
        else:
            # simple object
            if 'format' in structmap_data:
                item['contentFile'] = getHostedContentFile(structmap_data)
    else:
        item['harvest_type'] = 'harvested'
        if 'url_item' in item:
            if item['url_item'].startswith('http://ark.cdlib.org/ark:'):
                item['oac'] = True
                item['url_item'] = item['url_item'].replace(
                    'http://ark.cdlib.org/ark:',
                    'http://oac.cdlib.org/ark:')
                item['url_item'] = item['url_item'] + '/?brand=oac4'
            else:
                item['oac'] = False
        #TODO: error handling 'else'

    item['parsed_repository_data'] = []
    item['institution_contact'] = []

    col_ids = [parse_col_id(col_url) for col_url in item.get('collection_url')]
    item['collection_objects'] = [Collection(col_id) for col_id in col_ids]

    facet_sets = item['collection_objects'][0].get_facet_sets()

    print(set(item.keys()).intersection(set(METADATA_FIELDS)))

    clusters = {}
    for facet_set in facet_sets:
        facet = facet_set['facet_field'].facet
        metadata_arr = item.get(facet)
        if metadata_arr:
            for metadata_value in metadata_arr:
                value = [v for v in facet_set['values'] if v['label'] == metadata_value][0]
                if value['count'] > 1:
                    print(value)
                    
    for repository_data in item.get('repository_data'):
        item['parsed_repository_data'].append(
            getRepositoryData(repository_data=repository_data))

        institution_url = item['parsed_repository_data'][0]['url']
        institution_details = json_loads_url(institution_url +
                                             "?format=json")
        if 'ark' in institution_details and institution_details[
                'ark'] != '':
            contact_information = json_loads_url(
                "http://dsc.cdlib.org/institution-json/" +
                institution_details['ark'])
        else:
            contact_information = ''

        item['institution_contact'].append(contact_information)

    meta_image = False
    if item.get('reference_image_md5', False):
        meta_image = urllib.parse.urljoin(
            settings.UCLDC_FRONT,
            '/crop/999x999/{0}'.format(
                item['reference_image_md5']),
        )

    if item.get('rights_uri'):
        uri = item.get('rights_uri')
        item['rights_uri'] = {
            'url': uri,
            'statement': RIGHTS_STATEMENTS[uri]
        }

    ## do this w/o multiple returns?
    fromItemPage = request.META.get("HTTP_X_FROM_ITEM_PAGE")
    item_id_query = QueryDict(f'itemId={item_id}')
    if fromItemPage:
        return render(
            request, 'calisphere/itemViewer.html', {
                'q': '',
                'item': item,
                'item_solr_search': item_solr_search,
                'meta_image': meta_image,
                'repository_id': None,
                'itemId': None,
            })
    search_results = {'reference_image_md5': None}
    search_results.update(item)
    related_collections, num_related_collections = getRelatedCollections(item_id_query)
    carousel_search_results, carousel_numFound = itemViewCarouselMLT(item_id)
    return render(
        request, 'calisphere/itemView.html', {
            'q': '',
            'item': search_results,
            'item_solr_search': item_solr_search,
            'meta_image': meta_image,
            'rc_page': None,
            'related_collections': related_collections,
            'slug': None,
            'title': None,
            'num_related_collections': num_related_collections,
            'rq': None,
            'search_results': carousel_search_results,
            'numFound': carousel_numFound,
            'mlt': True, 
        })
