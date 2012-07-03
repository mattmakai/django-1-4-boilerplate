from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime, date
from random import choice, sample
from models import AppUpdate, Feedback
from core.models import Excellian
from common import _jsonResponse, _slugit
import json, re, urlparse


TEMPLATE_PATH = 'core/'
URL_PATH = '/'

def _createParams(req):
  p = {'breadcrumbs': []}
  p.update(csrf(req))
  return p


@csrf_protect
def signIn(req):
  if req.method == 'GET':
    if req.user.is_authenticated():
      return HttpResponseRedirect('/dashboard/')
    p = _createParams(req)
    p['is_signin'] = True
    return render_to_response(TEMPLATE_PATH + 'signin.html', p,
      context_instance=RequestContext(req))
  elif req.method == 'POST':
    username = req.POST.get('email', '')
    password = req.POST.get('password', '')
    user = authenticate(username=username, password=password)
    if user is None:
      return _jsonResponse('Invalid sign in.')
    elif user.is_active:
      login(req, user)
      return _jsonResponse({'redirect': '/dashboard/'})
    else:
      return _jsonResponse("Unable to log in.")


@login_required
def signOut(req):
  logout(req)
  return HttpResponseRedirect('/')


@login_required
def appUpdates(req):
  p = {'is_app_updates': True,
    'updates': AppUpdate.objects.all().order_by('-app_update_datetime')}
  return render_to_response(TEMPLATE_PATH + 'app_updates.html', p,
    context_instance=RequestContext(req))


@login_required
@csrf_protect
def feedback(req):
  if req.method == 'GET':
    p = {'excellian': req.user.get_profile(), 'is_feedback': True,
      'feedback': Feedback.objects.all().order_by('-message_date')}
    p.update(csrf(req))
    return render_to_response(TEMPLATE_PATH + "feedback.html", p, 
      context_instance=RequestContext(req))
  elif req.method == 'POST':
    feedback = Feedback()
    feedback.excellian = req.user.get_profile()
    feedback.message = req.POST.get('message', '').strip()
    feedback.slug = _slugit(Feedback, feedback.message)
    if feedback.message == '':
      return _jsonResponse('Please enter a feedback message.')
    feedback.save()
    messages.add_message(req, messages.INFO, 'Feedback received. Thanks!')
    return _jsonResponse({'redirect': '/feedback/'})


@login_required
@csrf_protect
def changePassword(req):
  u = req.user.get_profile().user
  current_pw = req.POST.get('current_password', '')
  new_pw1 = req.POST.get('new_password1', '')
  new_pw2 = req.POST.get('new_password2', '')
  if u.check_password(current_pw):
    if new_pw1 != new_pw2:
      return _jsonResponse("New passwords must match!")
    if new_pw1 == '' or new_pw2 == '':
      return _jsonResponse("Passwords must not be empty!")
    u.set_password(new_pw1)
    u.save()
    messages.add_message(req, messages.INFO, 'Password changed successfully.')
    return _jsonResponse({'redirect': '/my-settings/',})
  else:
    return _jsonResponse("Current password is incorrect.")


@login_required
def myProfile(req):
  p = {'is_my_account': True, 'messages': messages.get_messages(req)}
  p['breadcrumbs'] = [{'/my-profile/': 'My Profile'}]
  p.update(csrf(req))
  return render_to_response(TEMPLATE_PATH + 'my_profile.html', p,
    context_instance=RequestContext(req))


@login_required
def mySettings(req):
  if req.method == 'GET':
    p = {'is_my_account': True, 'breadcrumbs': \
      [{'/my-settings/': 'My Settings'}]}
    p.update(csrf(req))
    return render_to_response(TEMPLATE_PATH + 'my_settings.html', p,
      context_instance=RequestContext(req))


@login_required
@csrf_protect
def about(req):
  p = {'is_about': True, 'breadcrumbs': \
    [{'/about/': 'About'}]}
  p.update(csrf(req))
  return render_to_response(TEMPLATE_PATH + 'about.html', p,
    context_instance=RequestContext(req))
