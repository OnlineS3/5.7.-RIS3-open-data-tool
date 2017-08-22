# -*- coding: utf-8 -*-
import json
import os
import plotly.figure_factory as ff
from plotly.offline import plot
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count
from django.http import FileResponse
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.datastructures import MultiValueDictKeyError

from OpenDataTool.models import *
from OpenDataTool.settings import STATIC_ROOT
from .forms import *


def about(request):
    return render(request, 'about.html')


def guidepage(request):
    return render(request, 'guide.html')


def guide(request):
    path = os.path.join(STATIC_ROOT, 'data', 'OpenDataToolGuideline.pdf')
    if not os.path.exists(path):
        raise Http404()
    else:
        return FileResponse(open(path, 'rb'), content_type='application/pdf')


def related(request):
    return render(request, 'related.html')


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('about')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


def search(request):
    form = SearchForm()
    form2 = ExplorerForm()
    form3 = Explorer2Form()
    return render(request, 'search.html', {
        'form': form, 'form2': form2, 'form3': form3
    })


def results(request):
    res = []
    comparison = []

    region_filter = request.POST.getlist('region')
    regions = Region.objects.filter(code__in=Organisation.objects.exclude(regionCode__code__isnull=True).values_list('regionCode').distinct()) if region_filter == [] else Region.objects.filter(code__in=region_filter)

    for region in regions:
        if region.level < 3:
            region_t = region.get_all_children()
        else:
            region_t = [region]

        filter_kwargs = {'organisation__regionCode__in': [r.code for r in region_t]}
        if 'objective' in request.POST and request.POST.get('objective') != '':
            filter_kwargs['project__objective__icontains'] = request.POST.get('objective')
        if 'industry' in request.POST and request.POST.get('industry') != '':
            filter_kwargs['project__id__in'] = ProjectIndustry.objects.filter(industry=request.POST.get('industry')).values_list("project")
        project_organisations = ProjectOrganisation.objects.filter(**filter_kwargs).order_by('project__startDate')

        organisations = Organisation.objects.filter(id__in=project_organisations.values('organisation'))
        projects = Project.objects.filter(id__in=project_organisations.values('project'))

        if projects.count() > 0:
            for project in projects.values_list('startDate', 'endDate')[::-1]:
                comparison.append(dict(Task=region.nutsCode, Start=project[0], Finish=project[1]))

            result = {
                "region": region,
                "organisations": organisations,
                "projects": projects
            }
            res.append(result)

    comparison_fig = ff.create_gantt(comparison, colors=['rgb(106, 120, 141)'], showgrid_x=True, group_tasks=True, title=request.POST.get('objective'))
    comparison_graph = plot(comparison_fig, include_plotlyjs=True, output_type='div', show_link=False)

    return render(request, 'results.html', {'results': res, 'comparison': comparison_graph})


def explorer(request):
    if 'region' in request.POST:
        regions = {}
        region_codes = request.POST.getlist('region')

        for region in region_codes:
            industries = ProjectOrganisation.objects.filter(organisation__regionCode=region, project__projectindustry__industry__isnull=False).values('project__projectindustry__industry').annotate(Count('id'))
            results = []
            total = 0
            for industry in industries:
                ind = Industry.objects.get(id=industry['project__projectindustry__industry'])
                ids = ProjectOrganisation.objects.filter(organisation__regionCode=region, project__projectindustry__industry=ind.id)
                res = {'name': ind.name,
                       'count': industry['id__count'],
                       'organisations': Organisation.objects.filter(id__in=ids.values_list('organisation')),
                       'projects': Project.objects.filter(id__in=ids.values_list('project'))
                       }
                total += int(res['count'])
                results.append(res)

            for res in results:
                res['p'] = res['count']/float(total)

            regions[Region.objects.get(code=region).nutsCode] = sorted(results, key=lambda k: (len(k['projects']), k['count']), reverse=True)

        return render(request, 'explorer.html', {'results': regions})

    elif 'industries' in request.POST:
        industries = {}
        industry_codes = request.POST.getlist('industries')

        for industry in industry_codes:
            regions = ProjectOrganisation.objects.filter(project__projectindustry__industry=industry, organisation__regionCode__isnull=False).values('organisation__regionCode__code').annotate(count=Count('organisation'))
            results = []
            total = 0
            for region in regions:
                r = Region.objects.get(code=region['organisation__regionCode__code'])
                ids = ProjectOrganisation.objects.filter(organisation__regionCode=r.code, project__projectindustry__industry=industry)
                res = {'name': r.nutsCode,
                       'count': region['count'],
                       'organisations': Organisation.objects.filter(id__in=ids.values_list('organisation')),
                       'projects': Project.objects.filter(id__in=ids.values_list('project'))
                       }
                total += int(res['count'])
                results.append(res)

            for res in results:
                res['p'] = res['count']/float(total)

            industries[Industry.objects.get(id=industry).name] = sorted(results, key=lambda k: (len(k['projects']), k['count']), reverse=True)

        return render(request, 'explorer.html', {'results': industries})


def projects(request):
    res = Project.objects.filter(id__in=request.POST.getlist('id'))
    return render(request, 'projects.html', {'projects': res})


# def init(request):
#     # response = urllib2.urlopen('http://cordis.europa.eu/data/cordis-h2020projects.csv')
#     # projects_df = pd.read_table(response, quotechar='"', sep=';')
#     # projects_df.dropna(subset=['startDate', 'endDate'], inplace=True)
#     #
#     # for i, r in projects_df.iterrows():
#     #     p = Project()
#     #     p.id = r['id']
#     #     p.acronym = r['acronym']
#     #     p.status = r['status']
#     #     p.programme = r['programme']
#     #     p.topics = r['topics']
#     #     p.frameworkProgramme = r['frameworkProgramme']
#     #     p.title = r['title']
#     #     p.startDate = r['startDate']
#     #     p.endDate = r['endDate']
#     #     if r['projectUrl'] != "nan":
#     #         p.projectUrl = r['projectUrl']
#     #     p.objective = r['objective']
#     #     p.totalCost = str(r['totalCost']).replace(',', '.')
#     #     p.call = r['call']
#     #     p.fundingScheme = r['fundingScheme']
#     #     p.save()
#     #
#     # response = urllib2.urlopen('http://cordis.europa.eu/data/cordis-h2020organizations.csv')
#     # organisations_df = pd.read_table(response, quotechar='"', sep=';')
#     #
#     # for i, r in organisations_df.iterrows():
#     #     if Organisation.objects.filter(id=r['id']).count() == 0:
#     #         o = Organisation()
#     #         o.id = r['id']
#     #         o.name = r['name']
#     #         o.shortName = r['shortName']
#     #         o.activityType = r['activityType']
#     #         o.country = r['country']
#     #         o.street = r['street']
#     #         o.city = r['city']
#     #         o.postCode = r['postCode']
#     #         # o.regionCode = r['regionCode']
#     #         o.organizationUrl = r['organizationUrl']
#     #         o.save()
#     #
#     # for i, r in organisations_df.iterrows():
#     #     if Project.objects.filter(id=r['projectID']).count() == 1 and Organisation.objects.filter(id=r['id']).count() == 1:
#     #         o = ProjectOrganisation()
#     #         o.project_id = r['projectID']
#     #         o.organisation_id = r['id']
#     #         o.role = r['role']
#     #         o.endOfParticipation = r['endOfParticipation']
#     #         if pd.isnull(r['ecContribution']):
#     #             o.ecContribution = 0
#     #         else:
#     #             o.ecContribution = str(r['ecContribution']).replace(',', '.')
#     #         o.save()
#     #
#     # countries = ["AT", "BE", "BG", "CH", "CY", "CZ", "DE", "DK", "EE", "EL", "FI", "HR", "HU", "IS", "IT", "LI", "LT", "LU", "LV", "MT", "NL", "NO", "RO", "SI", "SK", "TR", "UK"]
#     #
#     # for country in countries:
#     #     organisations_qs = Organisation.objects.filter(country=country)
#     #     mapping_df = pd.read_table("C:\Users\Ryan Faulkner\Documents\Online S3\Region Data\hide\pc_" + country.lower() + "_NUTS-2010.txt", sep=';', dtype='str')
#     #
#     #     for organisation in organisations_qs:
#     #         res = mapping_df[mapping_df["CODE"] == organisation.postCode]
#     #         try:
#     #             if len(res["NUTS_3"] > 0):
#     #                 organisation.regionCode_id = Region.objects.get(nutsCode=res["NUTS_3"].iloc[0])
#     #                 organisation.save()
#     #         except Region.DoesNotExist:
#     #             print organisation.postCode
#
#     return HttpResponse("OK!")
#
#
# import json
# import requests
# import time
#
#
# class Kales(object):
#     def __init__(self, api_key):
#         self.api_key = api_key
#
#     def _request(self, content, content_type, **kwargs):
#         headers = {
#             "content-type": content_type,
#             "omitOutputtingOriginalText": "true",
#             "outputFormat": "application/json",
#             "x-ag-access-token": self.api_key,
#             "x-calais-language": "English"
#         }
#         headers.update(kwargs)
#         return requests.post("https://api.thomsonreuters.com/permid/calais", data=content, headers=headers)
#
#     def analyze(self, project, content, content_type="text/raw", **kwargs):
#         if not content or not content.strip():
#             return None
#
#         response = self._request(content, content_type, **kwargs)
#         response.raise_for_status()
#         content = json.loads(response.content)
#
#         for element in list(content.values()):
#             for key, value in list(element.items()):
#                 if isinstance(value, str) and value.startswith("http://") and value in content:
#                     element[key] = content[value]
#         for key, value in list(content.items()):
#             o = ProjectTopics()
#             o.project = project
#             if '_typeGroup' in value:
#                 o.typeGroup = value['_typeGroup']
#             if '_type' in value:
#                 o.type = value['_type']
#             if 'name' in value:
#                 o.name = value['name']
#             if 'importance' in value:
#                 o.importance = value['importance']
#             if 'relevance' in value:
#                 o.relevance = value['relevance']
#             if 'confidencelevel' in value:
#                 o.confidenceLevel = value['confidencelevel']
#             o.save()
#
#             if "_typeGroup" in value:
#                 group = value["_typeGroup"]
#                 if group not in content:
#                     content[group] = []
#                 del value["_typeGroup"]
#                 content[group].append(value)
#         return content
#
#
# def annotate(request):
#     kales = Kales(api_key="4rL1kyDbDvnJZQqtBipa1SAhCc9ovyLA")
#     projects = Project.objects.filter(id__in=ProjectOrganisation.objects.filter(organisation__regionCode__code__isnull=False).values_list('project')).exclude(id__in=ProjectTopics.objects.all().values_list('project').distinct())
#     for project in projects:
#         kales.analyze(project, project.title.encode('utf-8') + " " + project.objective.encode('utf-8'))
#         time.sleep(1)
#
#     # industries = ProjectTopics.objects.filter(typeGroup="industry").values_list("name").distinct()
#     # for industry in industries:
#     #     i = Industry()
#     #     i.name = industry[0].encode('utf-8').replace(' - NEC', '')
#     #     i.save()
#     #
#     # project_ind = ProjectTopics.objects.filter(typeGroup="industry")
#     # for p_i in project_ind:
#     #     o = ProjectIndustry()
#     #     o.project = p_i.project
#     #     o.industry = Industry.objects.filter(name=p_i.name.encode('utf-8').replace(' - NEC', ''))[0]
#     #     o.relevance = p_i.relevance
#     #     o.save()
#
#     return HttpResponse('OK!')


def query(request):
    bookmarks = Project.objects.filter(id__in=Bookmark.objects.filter(user=request.session['opendata_profile']['email']).values_list('project', flat=True))

    try:
        q = request.GET['query'].strip()
        c = request.GET['queryContext']
    except MultiValueDictKeyError:
        return render(request, 'query.html', {'query': ''})

    try:
        r = request.GET['show']
    except MultiValueDictKeyError:
        r = '10'

    try:
        s = request.GET['sort']
        if s == 'Query':
            s = c
        o = request.GET['order']
    except MultiValueDictKeyError:
        s = "startDate"
        o = ''

    if c == 'region':
        pro_org = ProjectOrganisation.objects.filter(organisation__regionCode__nutsCode__icontains=q)
        projects = Project.objects.filter(id__in=pro_org.values_list('project_id'))
        organisations = Organisation.objects.filter(id__in=pro_org.values_list('organisation_id'))
    else:
        filter_dict = {c + "__icontains": q}
        projects = Project.objects.filter(**filter_dict).order_by(o+s)
        if c == 'id':
            organisations = Organisation.objects.filter(id__in=ProjectOrganisation.objects.filter(project__in=projects.values_list('id')).values_list('organisation_id'))
            pro_org = ProjectOrganisation.objects.filter(project_id__in=projects.values_list('id')).values('organisation__shortName', 'organisation__name', 'organisation__street', 'organisation__city', 'organisation__country', 'organisation__postCode', 'organisation__regionCode__nutsCode', 'organisation__organizationUrl', 'organisation__activityType', 'role', 'endOfParticipation', 'ecContribution', 'project__totalCost')
        else:
            organisations = []
            pro_org = []

    no = projects.count()

    '''Pagination'''
    if r != 'All' and int(r):
        project_paginator = Paginator(projects, int(r))
    else:
        project_paginator = Paginator(projects, projects.count())

    try:
        project_page = project_paginator.page(request.GET['page'])
    except (PageNotAnInteger, MultiValueDictKeyError):
        project_page = project_paginator.page(1)
    except EmptyPage:
        project_page = project_paginator.page(project_paginator.num_pages)

    return render(request, 'query.html', {'query': q, 'queryContext': c, 'records': r, 'sort': s, 'no': no, 'projects': project_page, 'org': organisations, 'pro_org': pro_org, 'bookmarks': bookmarks})


def bookmarked(request):
    if request.method == 'POST' and 'opendata_profile' in request.session:
        bookmark = json.loads(request.body.decode('utf-8'))
        bm = Bookmark.objects.filter(user=request.session['opendata_profile']['email'], project_id=bookmark)
        if bm.exists():
            print 'Deleting Existing'
            bm.delete()
        else:
            print 'Adding New Bookmark'
            bm = Bookmark()
            bm.user = request.session['opendata_profile']['email']
            bm.project_id = bookmark
            bm.save()
        return HttpResponse('OK')
    return HttpResponse('Error')
