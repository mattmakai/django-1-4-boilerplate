from django.conf.urls.defaults import *

urlpatterns = patterns('blog.views',
  url(r'^$', 'blog', name="blog"),
	url(r'^search/$', 'search', name="blog_search"),
	url(r'^search/', 'search', name="blog_search"),
	url(r'^(?P<name>[a-zA-Z0-9\-]+)/$', 'view', name="blog_post"),
)

