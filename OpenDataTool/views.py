# -*- coding: utf-8 -*-
import os
import json
import StringIO
import pandas as pd
import plotly.figure_factory as ff
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count
from django.http import FileResponse, JsonResponse, HttpResponse, Http404
from django.shortcuts import render, redirect
from django.utils.datastructures import MultiValueDictKeyError
from plotly.offline import plot
from OpenDataTool.models import *
from OpenDataTool.settings import STATIC_ROOT
from .forms import *


def about(request):
    return render(request, 'about.html')


def guide(request):
    return render(request, 'guide.html')


def pdf(request):
    path = os.path.join(STATIC_ROOT, 'OpenDataToolGuideline.pdf')
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
    form2 = ExploreRegionForm()
    form3 = ExploreIndustryForm()
    return render(request, 'search.html', {
        'form': form, 'form2': form2, 'form3': form3
    })


def results(request):
    res = []
    comparison = []

    region_filter = request.POST.getlist('region')
    regions = Region.objects.filter(code__in=Organisation.objects.exclude(regionCode__code__isnull=True).values_list(
        'regionCode').distinct()) if region_filter == [] else Region.objects.filter(code__in=region_filter)

    for region in regions:
        if region.level < 3:
            region_t = region.get_all_children()
        else:
            region_t = [region]

        filter_kwargs = {'organisation__regionCode__in': [r.code for r in region_t]}
        if 'objective' in request.POST and request.POST.get('objective') != '':
            filter_kwargs['project__objective__icontains'] = request.POST.get('objective')
        if 'industry' in request.POST and request.POST.get('industry') != '':
            filter_kwargs['project__id__in'] = ProjectIndustry.objects.filter(
                industry=request.POST.get('industry')).values_list("project")
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

    comparison_fig = ff.create_gantt(comparison, colors=['rgb(106, 120, 141)'], showgrid_x=True, group_tasks=True,
                                     title=request.POST.get('objective'))
    comparison_graph = plot(comparison_fig, include_plotlyjs=True, output_type='div', show_link=False)

    return render(request, 'results.html', {'results': res, 'comparison': comparison_graph})


def explorer(request):
    if 'region' in request.POST:
        regions = {}
        region_codes = request.POST.getlist('region')

        for region in region_codes:
            industries = ProjectOrganisation.objects.filter(organisation__regionCode=region,
                                                            project__projectindustry__industry__isnull=False).values(
                'project__projectindustry__industry').annotate(Count('id'))
            results = []
            total = 0
            for industry in industries:
                ind = Industry.objects.get(id=industry['project__projectindustry__industry'])
                ids = ProjectOrganisation.objects.filter(organisation__regionCode=region,
                                                         project__projectindustry__industry=ind.id)
                res = {'name': ind.name,
                       'count': industry['id__count'],
                       'organisations': Organisation.objects.filter(id__in=ids.values_list('organisation')),
                       'projects': Project.objects.filter(id__in=ids.values_list('project'))
                       }
                total += int(res['count'])
                results.append(res)

            for res in results:
                res['p'] = res['count'] / float(total)

            regions[Region.objects.get(code=region).nutsCode] = sorted(results,
                                                                       key=lambda k: (len(k['projects']), k['count']),
                                                                       reverse=True)

        return render(request, 'explorer.html', {'results': regions})

    elif 'industries' in request.POST:
        industries = {}
        industry_codes = request.POST.getlist('industries')

        for industry in industry_codes:
            regions = ProjectOrganisation.objects.filter(project__projectindustry__industry=industry,
                                                         organisation__regionCode__isnull=False).values(
                'organisation__regionCode__code').annotate(count=Count('organisation'))
            results = []
            total = 0
            for region in regions:
                r = Region.objects.get(code=region['organisation__regionCode__code'])
                ids = ProjectOrganisation.objects.filter(organisation__regionCode=r.code,
                                                         project__projectindustry__industry=industry)
                res = {'name': r.nutsCode,
                       'count': region['count'],
                       'organisations': Organisation.objects.filter(id__in=ids.values_list('organisation')),
                       'projects': Project.objects.filter(id__in=ids.values_list('project'))
                       }
                total += int(res['count'])
                results.append(res)

            for res in results:
                res['p'] = res['count'] / float(total)

            industries[Industry.objects.get(id=industry).name] = sorted(results,
                                                                        key=lambda k: (len(k['projects']), k['count']),
                                                                        reverse=True)

        return render(request, 'explorer.html', {'results': industries})


def projects(request):
    res = Project.objects.filter(id__in=request.POST.getlist('id'))
    return render(request, 'projects.html', {'projects': res})


def query(request):
    if 'opendata_profile' in request.session:
        bookmarks = Project.objects.filter(
            id__in=Bookmark.objects.filter(user=request.session['opendata_profile']['email']).values_list('project', flat=True))
    else:
        bookmarks = []

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
        filter_dict = {'organisation__regionCode__nutsCode__icontains': q}
        try:
            filter_dict['project__objective__icontains'] = request.GET['topic']
        except MultiValueDictKeyError:
            pass
        pro_org = ProjectOrganisation.objects.filter(**filter_dict)
        projects = Project.objects.filter(id__in=pro_org.values_list('project_id'))
        organisations = Organisation.objects.filter(id__in=pro_org.values_list('organisation_id'))
    else:
        if c == 'id':
            filter_dict = {c: q}
        else:
            filter_dict = {c + "__icontains": q}
        projects = Project.objects.filter(**filter_dict).order_by(o + s)
        if c == 'id' or c == 'objective':
            organisations = Organisation.objects.filter(id__in=ProjectOrganisation.objects.filter(project__in=projects.values_list('id')).values_list('organisation_id'))
            pro_org = ProjectOrganisation.objects.filter(project_id__in=projects.values_list('id')).values(
                'organisation__shortName', 'organisation__name', 'organisation__street', 'organisation__city',
                'organisation__country', 'organisation__postCode', 'organisation__regionCode__nutsCode',
                'organisation__organizationUrl', 'organisation__activityType', 'role', 'endOfParticipation',
                'ecContribution', 'project__totalCost')
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

    if s not in ["startDate", "endDate"]:
        s = "Query"

    return render(request, 'query.html', {'query': q, 'queryContext': c, 'records': r, 'sort': s, 'order': o, 'no': no,
                                          'projects': project_page, 'org': organisations, 'pro_org': pro_org,
                                          'bookmarks': bookmarks})


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


def exporter(request):
    return render(request, 'exporter.html')


def export(request):
    if request.method == 'POST':
        filter_dict = {k: v for k, v in request.POST.items() if v}
        del filter_dict['csrfmiddlewaretoken']
        qs = ProjectOrganisation.objects.filter(**filter_dict).select_related("project", "organisation")

    if request.method == 'GET':
        if 'bookmarks' in request.GET:
            qs = ProjectOrganisation.objects.filter(project_id__in=Bookmark.objects.filter(
                user=request.session['opendata_profile']['email'])).select_related("project", "organisation")
        else:
            qs = ProjectOrganisation.objects.all().select_related("project", "organisation")

    df = pd.DataFrame(list(
        qs.values('project__acronym', 'project__title', 'project__objective', 'project__status', 'project__projectUrl',
                  'project__fundingScheme', 'project__call', 'project__totalCost', 'project__projectindustry__industry',
                  'project__topics', 'organisation__name', 'organisation__shortName', 'organisation__activityType',
                  'organisation__regionCode__description', 'organisation__city', 'organisation__country',
                  'organisation__organizationUrl', 'role', 'endOfParticipation', 'ecContribution')))

    io = StringIO.StringIO()

    writer = pd.ExcelWriter('temp.xlsx', engine='xlsxwriter')
    writer.book.filename = io

    df.to_excel(writer, sheet_name='Successful Grant Applications')
    writer.save()

    response = HttpResponse(io.getvalue(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=RIS3_OpenDataTool_Export.xlsx"

    return response


def map(request):
    return render(request, 'map.html')


def map_data(request):
    if request.is_ajax():
        sql = """SELECT 1 AS id, nutsCode AS code, nutsCode || ' - ' || OpenDataTool_region.description AS label, latitude, longitude, COUNT(project_id) AS projects FROM OpenDataTool_projectorganisation
                 LEFT OUTER JOIN OpenDataTool_organisation ON OpenDataTool_projectorganisation.organisation_id = OpenDataTool_organisation.id
                 LEFT OUTER JOIN OpenDataTool_project ON OpenDataTool_projectorganisation.project_id = OpenDataTool_project.id
                 LEFT OUTER JOIN OpenDataTool_region ON OpenDataTool_organisation.regionCode_id = OpenDataTool_region.code
                 WHERE objective LIKE '%{}%'
                 GROUP BY regionCode_id""".format(request.POST.get('term', ''))
        data = {}
        for c in Organisation.objects.raw(sql):
            data[c.code] = {'label': c.label, 'latitude': c.latitude, 'longitude': c.longitude, 'projects': c.projects}
        return JsonResponse(json.dumps(data), safe=False)
