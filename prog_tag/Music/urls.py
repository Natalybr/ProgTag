from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
admin.autodiscover()



urlpatterns = patterns('',
    
    url(r'^$', 'musicapp.views.index'),
    url(r'^get_labels$', 'musicapp.views.get_labels'),
    url(r'^get_song_graph_json$', 'musicapp.views.get_song_graph_json')
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)