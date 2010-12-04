import base64, datetime, math
from decimal import Decimal
from time import strptime

from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect
from chezbob.users.models import User


@login_required
def user_list(request):
    users = list(User.objects.all())

    return render_to_response('users/user_list.html',
                              {'user': request.user,
                               'title': "User Overview",
                               'users': users})



@login_required
def user_details(request):
    users = list(User.objects.all())

    return render_to_response('users/user_list.html',
                              {'user': request.user,
                               'title': "User Overview",
                               'users': users})
