from .collection import getCollectionData, getFullCollection
from .repository import getRepositoryData, getFullRepository
from .constants import collection_template, repository_template

def collectionFilterDisplay(filter_item):
    collection = getFullCollection(
        collection_template.format(filter_item))
    collection.pop('local_id', None)
    collection.pop('slug', None)
    return collection

def repositoryFilterDisplay(filter_item):
    repository = getFullRepository(
        repository_template.format(filter_item))
    repository.pop('local_id', None)
    return repository


FACET_FILTER_TYPES = [{
    'facet': 'type_ss',
    'display_name': 'Type of Item',
    'filter': 'type_ss',
    'filter_transform': lambda filterVal : filterVal,
    'facet_transform': lambda facetVal : facetVal,
    'filter_display': lambda filterVal : filterVal
}, {
    'facet': 'facet_decade',
    'display_name': 'Decade',
    'filter': 'facet_decade',
    'filter_transform': lambda filterVal : filterVal,
    'facet_transform': lambda facetVal : facetVal,
    'filter_display': lambda filterVal : filterVal
}, {
    'facet': 'repository_data',
    'display_name': 'Contributing Institution',
    'filter': 'repository_url',
    'filter_transform': lambda filterVal : repository_template.format(filterVal),
    'facet_transform': lambda facetVal : getRepositoryData(repository_data=facetVal),
    'filter_display': lambda filterVal : repositoryFilterDisplay(filterVal)
}, {
    'facet': 'collection_data',
    'display_name': 'Collection',
    'filter': 'collection_url',
    'filter_transform': lambda filterVal : collection_template.format(filterVal),
    'facet_transform': lambda facetVal : getCollectionData(collection_data=facetVal),
    'filter_display': lambda filterVal : collectionFilterDisplay(filterVal)
}]

# FACETS are retrieved from Solr for a user to potentially FILTER on
# FILTERS are FACETS that have been selected by the user already
# We use more robust solr fields for a FACET (_data)
# so we don't have to hit registry for a repository name just to enumerate available FACETS
# We use more specific solr fields for a FILTER (_url)
# so if there is a change in some of the robust data and a harvest hasn't been run (ie - a collection name changes)
# the FILTER still works

# Make a copy of FACET_FILTER_TYPES to reset to original.
DEFAULT_FACET_FILTER_TYPES = FACET_FILTER_TYPES[:]