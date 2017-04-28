import numpy as np
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.datastructures import MultiValueDictKeyError
import collections
import urllib
import urllib2
import json
import pandas as pd
import io
import requests

from OpenDataTool.models import Project, Organisation


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
    h2020projects = pd.read_table('C:\Users\Ryan Faulkner\Documents\Online S3\Applications\OpenDataTool\static\data\cordis-h2020projects.csv', quotechar='"', sep=';')
    project_frames.append(h2020projects)
    h2020organisations = pd.read_table('C:\Users\Ryan Faulkner\Documents\Online S3\Applications\OpenDataTool\static\data\cordis-h2020organizations.csv', quotechar='"', sep=';')
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


def update(request):
    # # Projects
    # # Read current version
    # existing_projects_df = pd.DataFrame(list(Project.objects.all().values()))
    # # Read published
    # response = urllib2.urlopen('http://cordis.europa.eu/data/cordis-h2020projects.csv')
    # new_projects_df = pd.read_table(response, quotechar='"', sep=';')
    # new_projects_df.columns.values[0] = 'rcn'
    # new_projects_df['id'] = new_projects_df['id'].astype(str)
    #
    # updates_projects_df = existing_projects_df.merge(new_projects_df, on='id', how='outer', suffixes=['_1', '_2'])
    #
    # status_update = (updates_projects_df.status_1 != updates_projects_df.status_2)
    # extended = (updates_projects_df.endDate_1 != updates_projects_df.endDate_2)
    # to_update = status_update | extended
    #
    # for i, r in updates_projects_df[to_update].iterrows():
    #     project = Project.objects.get(pk=r['id'])
    #     project.status = r['status_2']
    #     project.endDate = r['endDate_2']
    #     project.save()

    # Organisations
    # Read current version
    existing_organisations_df = pd.DataFrame(list(Organisation.objects.all().values()))

    # Read published
    response = urllib2.urlopen('http://cordis.europa.eu/data/cordis-h2020organizations.csv')
    new_organisations_df = pd.read_table(response, quotechar='"', sep=';')
    new_organisations_df['id'] = new_organisations_df['id'].astype(str)

    updates_organisations_df = existing_organisations_df.merge(new_organisations_df, on=['id', 'projectAcronym'], how='outer', suffixes=['_1', '_2'])

    participation_ended = (updates_organisations_df.endOfParticipation_1 != updates_organisations_df.endOfParticipation_2)
    # role_change = (updates_organisations_df.role_1 != updates_organisations_df.role_2)
    to_update = participation_ended  # | role_change

    for i, r in updates_organisations_df[to_update].iterrows():
        if Organisation.objects.filter(id=r['id'], projectAcronym=r['projectAcronym']).count() > 0:
            print 'UPDATE'
            organisation = Organisation.objects.get(pk=r['id'])
            organisation.role = r['role_2']
            organisation.endOfParticipation = r['endOfParticipation_2']
        else:
            print 'INSERT: ' + r['shortName_2'] + ', ' + r['projectAcronym']
            organisation = Organisation()
            organisation.projectRcn = r['\xef\xbb\xbfprojectRcn']
            organisation.projectId = r['projectID']
            organisation.projectID_id = r['projectID']
            organisation.projectAcronym = r['projectAcronym']
            organisation.role = r['role_2']
            organisation.id = r['id']
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
    # H2020 Projects
    response = urllib2.urlopen('http://cordis.europa.eu/data/cordis-h2020projects.csv')
    p_df = pd.read_table(response, quotechar='"', sep=';')
    for i, r in p_df.iterrows():
        project = Project()
        project.rcn = r['\xef\xbb\xbfrcn']
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

    # H2020 Organisations
    response = urllib2.urlopen('http://cordis.europa.eu/data/cordis-h2020organizations.csv')
    o_df = pd.read_table(response, quotechar='"', sep=';')
    o_df = o_df[np.isfinite(o_df['projectID'])]
    for i, r in o_df.iterrows():
        organisation = Organisation()
        organisation.projectRcn = r['\xef\xbb\xbfprojectRcn']
        organisation.projectId = r['projectID']
        organisation.projectID_id = r['projectID']
        organisation.projectAcronym = r['projectAcronym']
        organisation.role = r['role']
        organisation.id = r['id']
        organisation.name = r['name']
        organisation.shortName = r['shortName']
        organisation.activityType = r['activityType']
        organisation.endOfParticipation = r['endOfParticipation']
        organisation.ecContribution = r['ecContribution']
        organisation.country = r['country']
        organisation.street = r['street']
        organisation.city = r['city']
        organisation.postCode = r['postCode']
        organisation.organizationUrl = r['organizationUrl']
        organisation.contactType = r['contactType']
        organisation.contactTitle = r['contactTitle']
        organisation.contactFirstNames = r['contactFirstNames']
        organisation.contactLastNames = r['contactLastNames']
        organisation.contactFunction = r['contactFunction']
        organisation.contactTelephoneNumber = r['contactTelephoneNumber']
        organisation.contactFaxNumber = r['contactFaxNumber']
        organisation.contactEmail = r['contactEmail']
        organisation.save()

    return HttpResponse('OK')
