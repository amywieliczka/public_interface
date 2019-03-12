def is_complex(mediajson)
    if 'structMap' in mediajson:
        return True
    else:
        return False


def is_hosted(item):
    if ('structmap_url' in item and 
        isinstance(item['structmap_url'], list) and 
        len(item['structmap_url']) >= 1):
        return True
    else:
        return False


def complexObjectView(item, mediajson, componentIndex): 
    formats = [
        component['format']
        for component in mediajson['structMap']
        if 'format' in component
    ]

    item.update({
        'structMap': mediajson['structMap'],
        'componentCount': len(mediajson['structMap']),
        'multiFormat': True if len(set(formats)) > 1 else False,
        'has_fixed_thumb': True if 'reference_image_md5' in item else False,
    })

    if all(f == 'image' for f in formats):
        item['hasComponentCaptions'] = False
    else:
        item['hasComponentCaptions'] = True

    if componentIndex: 
        item['selected'] = False
        item['selectedComponentIndex'] = int(componentIndex)

        # put together component information
        component = mediajson['structMap'][componentIndex]
        component['selected'] = True
        # remove emptry strings from list
        for k, v in list(component.items()):
            if isinstance(v, list):
                if isinstance(v[0], str):
                    component[k] = [name for name in v if name.strip()]

        item['contentFile'] = getHostedContentFile(component)
        # remove empty lists and empty strings from dict
        item['selectedComponent'] = dict(
            (k, v) for k, v in list(component.items()) if v)

    else:
        item['selected'] = True
        item['contentFile'] = getHostedContentFile(mediajson)
        
        # if no contentFile, get first component contentFile
        if item['contentFile'] is None:
            component = mediajson['structMap'][0]
            item['contentFile'] = getHostedContentFile(component)

    return item


def itemView(request, item_id=''):
    componentIndex = request.GET.get('order')
    fromItemPage = request.META.get("HTTP_X_FROM_ITEM_PAGE")

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

    numFound = item_solr_search.numFound;
    item = item_solr_search.results[0]

    if is_hosted(item):
        item['harvest_type'] = 'hosted'
        mediajson_url = string.replace(item['structmap_url'],
                                   's3://static',
                                   'https://s3.amazonaws.com/static')
        mediajson = json_loads_url(mediajson_url)
        if is_complex(mediajson):
            item.update(complexObjectView(item, mediajson, componentIndex))
        else:
            item['contentFile'] = getHostedContentFile(mediajson)
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

    
    item['institution_contact'] = []

    item['parsed_collection_data'] = [getFullCollection(parseCollectionData(c)['url'])
        for c in item.get('collection_data')]

    item['parsed_repository_data'] = [getFullRepository(parseRepositoryData(r)['url'])
        for r in item.get('repository_data')]

    institution_url = item['parsed_repository_data'][0]['url']
    registry_repo = json_loads_url(institution_url + "?format=json")
    if 'ark' in registry_repo and registry_repo['ark'] != '':
        contact_information = json_loads_url(
            "http://dsc.cdlib.org/institution-json/" +
            registry_repo['ark'])
    else:
        contact_information = ''
    item['institution_contact'] = contact_information

    meta_image = False
    if item.get('reference_image_md5', False):
        meta_image = urllib.parse.urljoin(
            settings.UCLDC_FRONT,
            '/crop/999x999/{0}'.format(
                item['reference_image_md5']), )

    if item.get('rights_uri'):
        uri = item.get('rights_uri')
        item['rights_uri'] = {
            'url': uri,
            'statement': RIGHTS_STATEMENTS[uri]
        }

    ## do this w/o multiple returns?
    fromItemPage = request.META.get("HTTP_X_FROM_ITEM_PAGE")
    if fromItemPage:
        return render(request, 'calisphere/itemViewer.html', {
            'q': '',
            'item': item,
            'item_solr_search': item_solr_search,
            'meta_image': meta_image,
            'repository_id': None,
            'itemId': None,
        })
    search_results = {'reference_image_md5': None}
    search_results.update(item)
    return render(request, 'calisphere/itemView.html', {
        'q': '',
        'item': search_results,
        'item_solr_search': item_solr_search,
        'meta_image': meta_image,
        'rc_page': None,
        'related_collections': None,
        'slug': None,
        'title': None,
        'num_related_collections': None,
        'rq': None,
    })
