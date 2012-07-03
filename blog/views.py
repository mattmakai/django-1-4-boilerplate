from models import BlogPost
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_protect
from django.template import RequestContext
import re

TEMPLATE_PATH = 'blog/'


def blog(req):
  """Returns the main screen of the blog."""
  blog_posts = BlogPost.objects.filter(visible=True).order_by('-pub_date')
  all_posts = BlogPost.objects.filter(visible=True).order_by('-pub_date')
  p = {'page_header': 'Our Blog', 'is_blog': True, \
    'blog_posts': blog_posts, 'all_posts': all_posts }
  if req.user.is_authenticated():
    p['is_signed_in'] = True
  p.update(csrf(req))
  return render_to_response(TEMPLATE_PATH + 'blog.html', p,
    context_instance=RequestContext(req))


def view(req, name):
  """Tries to display a blog post based on a slug name."""
  post = get_object_or_404(BlogPost, url=name, visible=True)
  all_posts = BlogPost.objects.filter(visible=True).order_by('-pub_date')
  p = {'page_header': post.title, 'is_blog': True, \
    'post': post, 'all_posts': all_posts }
  if req.user.is_authenticated():
    p['is_signed_in'] = True
  p.update(csrf(req))
  return render_to_response(TEMPLATE_PATH + 'post.html', p,
    context_instance=RequestContext(req))


@csrf_protect
def search(req):
  if isPOST(req):
    query_string = ''
    found_entries = None
    if ('search' in req.POST) and req.POST['search'].strip():
      query_string = req.POST['search']
      entry_query = get_query(query_string, ['title', 'content',])
      found_entries = BlogPost.objects.filter(entry_query).order_by('-pub_date')
      all_posts = BlogPost.objects.filter(visible=True).order_by('-pub_date')
      p = {'query_string': query_string, 'found_entries': found_entries , \
        'all_posts': all_posts}
      if req.user.is_authenticated():
        p['is_signed_in'] = True
      return render_to_response(TEMPLATE_PATH + 'search_results.html', p,
        context_instance=RequestContext(req))
    else:
      p = {'query_string': query_string, 'found_entries': [], \
        'all_posts': []}
      if req.user.is_authenticated():
        p['is_signed_in'] = True
      return render_to_response(TEMPLATE_PATH + 'search_results.html', p,
        context_instance=RequestContext(req))


def normalize_query(query_string, \
  findterms=re.compile(r'"([^"]+)"|(\S+)').findall, \
  normspace=re.compile(r'\s{2,}').sub):
  """Splits the query string in individual keywords, getting rid of 
  unnecessary spaces and grouping quotes words together."""
  return [normspace(' ', (t[0] or t[1]).strip()) \
    for t in findterms(query_string)]


def get_query(query_string, search_fields):
  query = None
  terms = normalize_query(query_string)
  for term in terms:
    or_query = None
    for field_name in search_fields:
      q = Q(**{"%s__icontains" % field_name: term})
      if or_query is None:
        or_query = q
      else:
        or_query = or_query | q
    if query is None:
      query = or_query
    else:
      query = query & or_query
  return query
