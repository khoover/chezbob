import base64, datetime, math
from decimal import Decimal
from time import strptime

from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect

##### Available queries to run #####
queries = {}
query_order = []
def add_query(name, description, query, variables):
    queries[name] = (description, query, variables)
    query_order.append(name)

add_query("accounts", "Account Balances",
          """select username, balance, last_seen, email
             from account_summary order by balance, lower(username)""",
          [])
add_query("inactive", "Newly-Inactive Products",
          """select * from bulk_items
             where
               bulkid not in
                 (select distinct bulkid from aggregate_purchases
                  where date >= '2010-04-01' and bulkid is not null)
               and active""",
          [])

##### Helper functions #####
def run_query(name, variables):
    """Run an SQL query directly against the database and return results.
       
    Returns a pair containing information about each database column, and the
    set of database results."""

    (description, query, variable_names) = queries[name]

    from django.db import connection
    cursor = connection.cursor()
    cursor.execute(query, variables)

    columns = [c[0] for c in cursor.description]
    data = cursor.fetchall()

    return {'name': name, 'description': description, 'query': query,
            'columns': columns, 'data': data}

##### Return a raw HTML table with query results #####
@login_required
def raw_table(request, query):
    results = run_query(query, [])

    response = HttpResponse(mimetype="text/html")
    response.write("<table>\n")
    response.write("<thead>\n")
    response.write("<tr>\n")
    for c in results['columns']:
	response.write("<th>" + c + "</th>\n")
    response.write("</tr>\n")
    response.write("</thead>\n")

    response.write("<tbody>\n")
    for row in results['data']:
	response.write("<tr>\n")
	for d in row:
	    response.write("<td>" + str(d) + "</td>\n")
	response.write("</tr>\n")
    response.write("</tbody>\n")

    response.write("</table>\n")

    return response

##### Page view functions (invoked by Django to display a page) #####
@login_required
def home(request):
    results = run_query("accounts", [])

    return render_to_response('query/home.html',
                              {'user': request.user, 'query': results})
