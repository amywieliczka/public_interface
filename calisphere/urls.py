from django.conf.urls import url
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.conf import settings
from calisphere.home import HomeView
from . import views
from . import collection_views
from . import item_views

app_name = 'calisphere'

urlpatterns = [
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^search/$', views.search, name='search'),
    url(r'^item/(?P<item_id>.*)/$', item_views.itemView, name='itemView'),
    url(r'^collections/$',
        collection_views.collectionsDirectory,
        name='collectionsDirectory'),
    url(r'^collections/(?P<collection_letter>[a-zA-Z]{1})/$',
        collection_views.collectionsAZ,
        name='collectionsAZ'),
    url(r'^collections/(?P<collection_letter>num)/$',
        collection_views.collectionsAZ,
        name='collectionsAZ'),
    url(r'^collections/(?P<collection_id>\d*)/$',
        collection_views.collectionSearch,
        name='collectionView'),
    url(r'^collections/(?P<collection_id>\d*)/reports/(?P<facet>[^/].*)/(?P<facet_value>.*)/$',
        views.reportCollectionFacetValue,
        name='reportCollectionFacetValue'),
    url(r'^collections/(?P<collection_id>\d*)/reports/(?P<facet>.*)/$',
        views.reportCollectionFacet,
        name='reportCollectionFacet'),
    url(r'^collections/(?P<collection_id>\d*)/(?P<cluster>[^/].*)/(?P<cluster_value>.*)/$',
        collection_views.collectionFacetValue,
        name='collectionFacetValue'),
    url(r'^collections/(?P<collection_id>\d*)/(?P<facet>.*)/$',
        collection_views.collectionFacet,
        name='collectionFacet'),
    url(r'^collections/(?P<collection_id>\d*)/(?P<facet>.*).json$',
        collection_views.collectionFacetJson,
        name='collectionFacetJson'),

    # Redirects to new 'exhibitions'
    url(r'^collections/themed/$',
        RedirectView.as_view(url='/exhibitions/'),
        name='themedCollections'),
    url(r'^collections/cal-cultures/$',
        RedirectView.as_view(url='/cal-cultures/'),
        name='calCultures'),
    url(r'^collections/jarda/$',
        RedirectView.as_view(url='/exhibitions/t11/jarda/'),
        name='jarda'),
    url(r'^collections/titleSearch/$',
        collection_views.collectionsSearch,
        name='collectionsTitleSearch'),
    url(r'^collections/titles.json$',
        collection_views.collectionsTitles,
        name='collectionsTitleData'),
    url(r'^institution/(?P<repository_id>\d*)(?:/(?P<subnav>items|collections))?/',
        views.repositoryView,
        name='repositoryView'),
    url(r'^(?P<campus_slug>UC\w{1,2})(?:/(?P<subnav>items|collections|institutions))?/',
        views.campusView,
        name='campusView'),
    url(r'^institutions/$', views.campusDirectory, name='campusDirectory'),
    url(r'^institutions/statewide-partners/$',
        views.statewideDirectory,
        name='statewideDirectory'),
    url(r'about/$',
        TemplateView.as_view(template_name='calisphere/about.html'),
        name='about'),
    url(r'help/$',
        TemplateView.as_view(template_name='calisphere/help.html'),
        name='help'),
    url(r'terms/$',
        TemplateView.as_view(template_name='calisphere/termsOfUse.html'),
        name='termsOfUse'),
    url(r'privacy/$',
        TemplateView.as_view(template_name='calisphere/privacyStatement.html'),
        name='privacyStatement'),
    url(r'outreach/$',
        TemplateView.as_view(template_name='calisphere/outreach.html'),
        name='outreach'),
    url(r'contribute/$',
        TemplateView.as_view(template_name='calisphere/contribute.html'),
        name='contribute'),
    url(r'jobs/$',
        TemplateView.as_view(template_name='calisphere/jobs.html'),
        name='jobs'),
    url(r'overview/$', 
        TemplateView.as_view(template_name='calisphere/overview.html'),
        name='overview'),
    url(r'posters/$', views.posters, name='posters'),
    url(r'sitemap-(?P<section>.*).xml$', views.sitemapSection),
    url(r'sitemap-(?P<section>.*).xml.gz$', views.sitemapSectionZipped),

    # AJAX HELPERS
    url(r'^relatedCollections/',
        views.relatedCollections,
        name='relatedCollections'),
    url(r'^relatedExhibitions',
        views.relatedExhibitions,
        name='relatedExhibitions'),
    url(r'^carousel/', views.itemViewCarousel, name='carousel'),
    url(r'^contactOwner/', views.contactOwner, name='contactOwner'),
]

if settings.UCLDC_METADATA_SUMMARY:
    urlpatterns.insert(0,
        url(r'^collections/(?P<collection_id>\d*)/metadata/$',
            collection_views.collectionMetadata,
            name='collectionMetadata'),
    )
    urlpatterns.insert(0,
        url(r'^collections/(?P<collection_id>\d*)/browse/$',
            collection_views.collectionBrowse,
            name='collectionBrowse'),)
