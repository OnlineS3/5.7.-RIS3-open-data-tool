import numpy as np
import pandas as pd

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from django.http import Http404
from django.http import HttpResponse
from django.http import FileResponse

from django.shortcuts import render
from django.utils.datastructures import MultiValueDictKeyError

import os
import io
import json
import urllib
import urllib2
import requests
import collections

from django_pandas.io import read_frame

from OpenDataTool.models import Project, Organisation
from OpenDataTool.settings import STATIC_ROOT


def home(request):
    url = 'http://data.europa.eu/euodp/data/api/action/tag_list'
    response = urllib.urlopen(url)
    assert response.code == 200

    # Use the json module to load CKAN's response into a dictionary.
    response_dict = json.loads(response.read())

    # Check the contents of the response.
    assert response_dict['success'] is True
    result = response_dict['result']

    return render(request, 'search.html', {'tags': result})


def test(request):
    return render(request, 'result.html')


def resource(request):
    try:
        l = request.GET['l']
    except MultiValueDictKeyError:
        raise Http404("Resource not found")

    s = requests.get(l).content
    csv_df = pd.read_table(io.StringIO(s.decode('utf-8')), sep=',|\t')
    csv_df["geo\\time"] = csv_df["geo\\time"].map(lambda x: x.lower())

    return render(request, 'resource.html', {'meta': csv_df["geo\\time"], 'table': csv_df})


def search(request):
    try:
        q = request.GET['q']
    except MultiValueDictKeyError:
        q = ''

    try:
        r = int(request.GET['r'])
    except MultiValueDictKeyError:
        r = 10
    except ValueError:
        raise Http404("Page does not exist")

    try:
        p = int(request.GET['p'])
    except MultiValueDictKeyError:
        p = 0
    except ValueError:
        raise Http404("Page does not exist")

    # Load tags
    tag_url = 'http://data.europa.eu/euodp/data/api/action/tag_list'
    tag_response = urllib.urlopen(tag_url)
    assert tag_response.code == 200

    # Use the json module to load CKAN's response into a dictionary.
    tag_response_dict = json.loads(tag_response.read())

    # Check the contents of the response.
    assert tag_response_dict['success'] is True
    tag_result = tag_response_dict['result']

    # url = 'http://demo.ckan.org/api/3/action/package_search'
    url = 'http://data.europa.eu/euodp/data/api/action/package_search'

    # Use the json module to dump a dictionary to a string for posting.
    data_string = urllib.quote(json.dumps({'q': q,
                                           'start': p * r,
                                           'rows': r
                                           }))

    # Make the HTTP request.
    response = urllib2.urlopen(url, data_string)
    assert response.code == 200

    # Use the json module to load CKAN's response into a dictionary.
    response_dict = json.loads(response.read())

    # Check the contents of the response.
    assert response_dict['success'] is True
    result = response_dict['result']

    pagination = {'page': p+1, 'start': (p*r)+1, 'end': (p*r)+r, 'next': p+1, 'previous': p-1, 'hide_next': '', 'hide_prev': ''}
    hidden = 'hidden'
    if pagination['previous'] < 0:
        pagination['hide_prev'] = hidden
    if pagination['next']*r >= result['count']:
        pagination['hide_next'] = hidden

    pages = collections.OrderedDict()
    for i in range(0, result['count'], r):
        idx = (i/r)
        if idx != p:
            pages[i/r] = (i/r)+1

    return render(request, 'results.html',
                  {'query': q, 'result': result, 'pages': pages, 'pagination': pagination, 'rows': r, 'tags': tag_result})


def about(request):
    return render(request, 'about.html')


def guide(request):
    path = os.path.join(STATIC_ROOT, 'data', 'OpenDataToolGuideline.pdf')
    if not os.path.exists(path):
        raise Http404()
    else:
        return FileResponse(open(path, 'rb'), content_type='application/pdf')


def related(request):
    return render(request, 'related.html')


def projects(request):
    bookmarks = []
    if 'bookmarks' in request.session:
        bookmarks = request.session['bookmarks']

    frameworks = []
    project_frames = []
    organisation_frames = []

    fp5 = fp6 = fp7 = ''

    if 'fp5' in request.GET:
        fp5 = request.GET['fp5']
    if 'fp6' in request.GET:
        fp6 = request.GET['fp6']
    if 'fp7' in request.GET:
        fp7 = request.GET['fp7']

    frameworks.append('h2020')

    h2020projects = Project.objects.all().to_dataframe()
    project_frames.append(h2020projects)

    h2020organisations = Organisation.objects.all().to_dataframe()
    organisation_frames.append(h2020organisations)

    if fp7 == 'on':
        frameworks.append('fp7')
        fp7projects = pd.read_table('C:\Users\Ryan Faulkner\Documents\Online S3\Applications\OpenDataTool\static\data\cordis-fp7projects.csv', quotechar='"', sep=';')
        fp7projects.columns.values[1] = 'id'
        project_frames.append(fp7projects)
        fp7organisations = pd.read_table('C:\Users\Ryan Faulkner\Documents\Online S3\Applications\OpenDataTool\static\data\cordis-fp7organizations.csv', quotechar='"', sep=';')
        fp7organisations.columns.values[1] = 'projectID'
        organisation_frames.append(fp7organisations)

    if fp6 == 'on':
        frameworks.append('fp6')
        fp6projects = pd.read_table('C:\Users\Ryan Faulkner\Documents\Online S3\Applications\OpenDataTool\static\data\cordis-fp6projects.csv', quotechar='"', sep=';')
        fp6projects.columns.values[1] = 'id'
        project_frames.append(fp6projects)
        fp6organisations = pd.read_table('C:\Users\Ryan Faulkner\Documents\Online S3\Applications\OpenDataTool\static\data\cordis-fp6organizations.csv', quotechar='"', sep=';')
        fp6organisations.columns.values[1] = 'projectID'
        organisation_frames.append(fp6organisations)

    if fp5 == 'on':
        frameworks.append('fp5')
        fp5projects = pd.read_table('C:\Users\Ryan Faulkner\Documents\Online S3\Applications\OpenDataTool\static\data\cordis-fp5projects.csv', quotechar='"', sep=';')
        fp5projects.columns.values[1] = 'id'
        project_frames.append(fp5projects)
        fp5organisations = pd.read_table('C:\Users\Ryan Faulkner\Documents\Online S3\Applications\OpenDataTool\static\data\cordis-fp5organizations.csv', quotechar='"', sep=';')
        organisation_frames.append(fp5organisations)

    # projects_df = pd.DataFrame()
    # if project_frames:
    projects_df = pd.concat(project_frames)
    projects_df = projects_df.dropna(subset=['id'])
    projects_df['id'] = projects_df['id'].astype(str)

    # organisations_df = pd.DataFrame()
    # if organisation_frames:
    organisations_df = pd.concat(organisation_frames)
    organisations_df = organisations_df.dropna(subset=['projectID'])
    organisations_df['projectID'] = organisations_df['projectID'].astype(str)

    '''Parameter Parsing'''
    try:
        q = request.GET['query']
    except MultiValueDictKeyError:
        q = ''

    try:
        c = request.GET['queryContext']
    except MultiValueDictKeyError:
        c = 'title'

    try:
        r = request.GET['show']
    except MultiValueDictKeyError:
        r = '10'

    try:
        s = request.GET['sort']
    except MultiValueDictKeyError:
        s = ''

    try:
        o = request.GET['order']
    except MultiValueDictKeyError:
        o = 'asc'

    '''Filtering'''
    projects_df = projects_df.dropna(subset=[c])
    projects_df = projects_df[projects_df[c].str.contains(q, case=False)]
    if c == 'id':
        organisations_df = organisations_df.dropna(subset=['projectID'])
        organisations_df = organisations_df[organisations_df['projectID'].str.contains(q, case=True)]
    elif c == 'coordinator':
        organisations_df = organisations_df.dropna(subset=['name'])
        organisations_df = organisations_df[organisations_df['name'].str.contains(q, case=False)]
    elif c == 'acronym':
        organisations_df = organisations_df.dropna(subset=['projectAcronym'])
        organisations_df = organisations_df[organisations_df['projectAcronym'].str.contains(q, case=False)]
    elif c == 'coordinatorCountry':
        organisations_df = organisations_df.dropna(subset=['country'])
        organisations_df = organisations_df[organisations_df['country'].str.contains(q, case=False)]
    else:
        organisations_df = pd.DataFrame()

    '''Sorting'''
    if s == 'Query':
        if o == 'a-z':
            projects_df.sort(c)
        else:
            projects_df.sort(c, ascending=False)
    if s == 'Start Date':
        projects_df = projects_df.ix[pd.to_datetime(projects_df.startDate).order().index]
        if o == 'dsc':
            projects_df.iloc[::-1]
    if s == 'End Date':
        projects_df = projects_df.ix[pd.to_datetime(projects_df.endDate).order().index]
        if o == 'dsc':
            projects_df.iloc[::-1]

    '''Pagination'''
    if r != 'All' and int(r):
        project_paginator = Paginator(projects_df.values, int(r))
    else:
        project_paginator = Paginator(projects_df.values, len(projects_df.index))

    try:
        p = request.GET['page']
    except MultiValueDictKeyError:
        p = 1

    try:
        project_page = project_paginator.page(p)
    except PageNotAnInteger:
        project_page = project_paginator.page(1)
    except EmptyPage:
        project_page = project_paginator.page(project_paginator.num_pages)

    # '''Retrieve Source Listing'''
    # url = 'http://data.europa.eu/euodp/data/api/action/package_search'
    #
    # # Use the json module to dump a dictionary to a string for posting.
    # data_string = urllib.quote(json.dumps({'q': 'CORDIS'}))
    #
    # # Make the HTTP request.
    # response = urllib2.urlopen(url, data_string)
    # assert response.code == 200
    #
    # # Use the json module to load CKAN's response into a dictionary.
    # response_dict = json.loads(response.read())
    #
    # # Check the contents of the response.
    # assert response_dict['success'] is True
    # result = response_dict['result']

    return render(request, 'projects.html', {'query': q,
                                             'queryContext': c,
                                             'records': r,
                                             'sort': s,
                                             'projects': project_page,
                                             # 'result': result,
                                             'org': organisations_df,
                                             'bookmarks': bookmarks,
                                             'fp': frameworks})


def bookmarked(request):
    if request.method == 'POST':
        bookmarks = json.loads(request.body.decode('utf-8'))
        request.session['bookmarks'] = bookmarks
        return HttpResponse('OK')
    return HttpResponse('Error')


def update_projects(request):
    # Projects
    # Read current version
    p_qs = Project.objects.all()
    existing_projects_df = p_qs.to_dataframe()

    # Read published
    response = urllib2.urlopen('http://cordis.europa.eu/data/cordis-h2020projects.csv')
    new_projects_df = pd.read_table(response, quotechar='"', sep=';')
    new_projects_df['id'] = new_projects_df['id'].astype(str)

    updates_projects_df = existing_projects_df.merge(new_projects_df, on='id', how='outer', suffixes=['_1', '_2'])

    status_update = (updates_projects_df.status_1 != updates_projects_df.status_2)
    extended = (updates_projects_df.endDate_1 != updates_projects_df.endDate_2)
    to_update = status_update | extended

    for i, r in updates_projects_df[to_update].iterrows():
        if Project.objects.filter(id=r['id']).count() > 0:
            project = Project.objects.get(pk=r['id'])
            project.status = r['status_2']
            project.endDate = r['endDate_2']
        else:
            project = Project()
            project.id = r['id']
            project.acronym = r['acronym_2']
            project.status = r['status_2']
            project.programme = r['programme_2']
            project.topics = r['topics_2']
            project.frameworkProgramme = r['frameworkProgramme_2']
            project.title = r['title_2']
            project.startDate = r['startDate_2']
            project.endDate = r['endDate_2']
            project.projectUrl = r['projectUrl_2']
            project.objective = r['objective_2']
            project.totalCost = r['totalCost_2']
            project.ecMaxContribution = r['ecMaxContribution_2']
            project.call = r['call_2']
            project.fundingScheme = r['fundingScheme_2']
            project.coordinator = r['coordinator_2']
            project.coordinatorCountry = r['coordinatorCountry_2']
            project.participants = r['participants_2']
            project.participantCountries = r['participantCountries_2']
            project.subjects = r['subjects_2']
        project.save()

    return HttpResponse('OK')


def update_organisations(request):
    # Organisations
    # Read current version
    existing_organisations_df = pd.DataFrame(list(Organisation.objects.all().values()))

    # Read published
    response = urllib2.urlopen('http://cordis.europa.eu/data/cordis-h2020organizations.csv')
    new_organisations_df = pd.read_table(response, quotechar='"', sep=';')
    new_organisations_df['id'] = new_organisations_df['id'].astype(str)
    new_organisations_df['projectID'] = new_organisations_df['projectID'].astype(str)

    updates_organisations_df = existing_organisations_df.merge(right=new_organisations_df, left_on=['projectID', 'organizationID'], right_on=['projectID', 'id'], how='outer', suffixes=['_1', '_2'])

    # pd.set_option('display.max_columns', None)
    # print updates_organisations_df.head(1)

    participation_ended = (updates_organisations_df.endOfParticipation_1 != updates_organisations_df.endOfParticipation_2)
    role_change = (updates_organisations_df.role_1 != updates_organisations_df.role_2)
    to_update = participation_ended | role_change

    for i, r in updates_organisations_df[to_update].iterrows():
        if Organisation.objects.filter(organizationID=r['organizationID'], projectID=r['projectID']).count() == 1:
            print "UPDATING ->" + r['projectAcronym_1']
            organisation = Organisation.objects.get(organizationID=r['organizationID'], projectID=r['projectID'])
            organisation.role = r['role_2']
            organisation.endOfParticipation = r['endOfParticipation_2']
        else:
            print "INSERTING ->" + r['projectAcronym_2']
            organisation = Organisation()
            organisation.projectID = r['projectID']
            organisation.projectAcronym = r['projectAcronym_2']
            organisation.role = r['role_2']
            organisation.organizationID = r['id_2']
            organisation.name = r['name_2']
            organisation.shortName = r['shortName_2']
            organisation.activityType = r['activityType_2']
            organisation.endOfParticipation = r['endOfParticipation_2']
            organisation.ecContribution = r['ecContribution_2']
            organisation.country = r['country_2']
            organisation.street = r['street_2']
            organisation.city = r['city_2']
            organisation.postCode = r['postCode_2']
            organisation.organizationUrl = r['organizationUrl_2']
            organisation.contactType = r['contactType_2']
            organisation.contactTitle = r['contactTitle_2']
            organisation.contactFirstNames = r['contactFirstNames_2']
            organisation.contactLastNames = r['contactLastNames_2']
            organisation.contactFunction = r['contactFunction_2']
            organisation.contactTelephoneNumber = r['contactTelephoneNumber_2']
            organisation.contactFaxNumber = r['contactFaxNumber_2']
            organisation.contactEmail = r['contactEmail_2']
        organisation.save()

    return HttpResponse('OK')


def initialise(request):
    Project.objects.all().delete()

    # H2020 Projects
    response = urllib2.urlopen('http://cordis.europa.eu/data/cordis-h2020projects.csv')
    p_df = pd.read_table(response, quotechar='"', sep=';')
    for i, r in p_df.iterrows():
        print r['acronym']
        project = Project()
        project.id = r['id']
        project.acronym = r['acronym']
        project.status = r['status']
        project.programme = r['programme']
        project.topics = r['topics']
        project.frameworkProgramme = r['frameworkProgramme']
        project.title = r['title']
        project.startDate = r['startDate']
        project.endDate = r['endDate']
        project.projectUrl = r['projectUrl']
        project.objective = r['objective']
        project.totalCost = r['totalCost']
        project.ecMaxContribution = r['ecMaxContribution']
        project.call = r['call']
        project.fundingScheme = r['fundingScheme']
        project.coordinator = r['coordinator']
        project.coordinatorCountry = r['coordinatorCountry']
        project.participants = r['participants']
        project.participantCountries = r['participantCountries']
        project.subjects = r['subjects']
        project.save()

    Organisation.objects.all().delete()

    # H2020 Organisations
    response = urllib2.urlopen('http://cordis.europa.eu/data/cordis-h2020organizations.csv')
    o_df = pd.read_table(response, quotechar='"', sep=';')
    o_df = o_df[np.isfinite(o_df['id'])]
    o_df = o_df[np.isfinite(o_df['projectID'])]

    o_df_records = o_df.to_dict('records')

    model_instances = [Organisation(
        projectID=r['projectID'],
        projectAcronym=r['projectAcronym'],
        role=r['role'],
        organizationID=r['id'],
        name=r['name'],
        shortName=r['shortName'],
        activityType=r['activityType'],
        endOfParticipation=r['endOfParticipation'],
        ecContribution=r['ecContribution'],
        country=r['country'],
        street=r['street'],
        city=r['city'],
        postCode=r['postCode'],
        organizationUrl=r['organizationUrl'],
        contactType=r['contactType'],
        contactTitle=r['contactTitle'],
        contactFirstNames=r['contactFirstNames'],
        contactLastNames=r['contactLastNames'],
        contactFunction=r['contactFunction'],
        contactTelephoneNumber=r['contactTelephoneNumber'],
        contactFaxNumber=r['contactFaxNumber'],
        contactEmail=r['contactEmail'],
    ) for r in o_df_records]

    Organisation.objects.bulk_create(model_instances)

    return HttpResponse('OK')


def notifications(request):
    notifications = []

    response = urllib2.urlopen('http://cordis.europa.eu/data/cordis-h2020projects.csv')
    updates = pd.read_table(response, quotechar='"', sep=';', dtype='str')
    updates.drop(updates.columns[0], axis=1, inplace=True)

    bookmarks = []
    if 'bookmarks' in request.session:
        bookmarks = request.session['bookmarks']

    for bookmark in bookmarks:
        project = Project.objects.get(pk=bookmark)

        df1 = read_frame(Project.objects.filter(id=bookmark))
        df1 = df1.iloc[0]
        df2 = updates[updates['id'] == bookmark].squeeze()

        if df1['status'] != df2['status']:
            notifications.append({"id": bookmark, "acronym": df1['acronym'], "message": "Status Update", "old": df1['status'], "new": df2['status']})
            project.status = df2['status']

        if df1['endDate'] != df2['endDate']:
            notifications.append({"id": bookmark, "acronym": df1['acronym'], "message": "Project Extended", "old": df1['endDate'], "new": df2['endDate']})
            project.endDate = df2['endDate']

        if df1['totalCost'] != df2['totalCost']:
            notifications.append({"id": bookmark, "acronym": df1['acronym'], "message": "Budget Update", "old": df1['totalCost'], "new": df2['totalCost']})
            project.totalCost = df2['totalCost']

        project.save()

        print notifications

        # print df1['acronym'] == df2['acronym']
        # print df1['title'] == df2['title']
        # print df1['objective'] == df2['objective']
        # print df1['projectUrl'] == df2['projectUrl']
        # print df1['totalCost'] == df2['totalCost']
        # print df1['ecMaxContribution'] == df2['ecMaxContribution']
        # print df1['coordinator'] == df2['coordinator']
        # print df1['participants'] == df2['participants']
        # print df1['subjects'] == df2['subjects']

    return render(request, 'notifications.html', {'notifications': notifications})

