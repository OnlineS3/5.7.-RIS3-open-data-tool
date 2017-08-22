# -*- coding:utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Region(models.Model):
    order = models.IntegerField()
    level = models.IntegerField()
    code = models.IntegerField(primary_key=True)
    parent = models.ForeignKey("self", blank=True, null=True)
    nutsCode = models.CharField(max_length=6)
    description = models.CharField(max_length=255)

    def __str__(self):
        if self.nutsCode != "nan":
            return self.nutsCode + " - " + self.description
        else:
            return self.description

    def get_all_children(self, include_self=True):
        r = []
        if include_self:
            r.append(self)
        for c in Region.objects.filter(parent__code=self.code):
            _r = c.get_all_children(include_self=True)
            if 0 < len(_r):
                r.extend(_r)
        return r


class Project(models.Model):
    id = models.IntegerField(primary_key=True)
    acronym = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    programme = models.CharField(max_length=100)
    topics = models.CharField(max_length=100)
    frameworkProgramme = models.CharField(max_length=5)
    title = models.CharField(max_length=250)
    startDate = models.DateField(blank=True, null=True)
    endDate = models.DateField(blank=True, null=True)
    projectUrl = models.URLField(blank=True, null=True)
    objective = models.CharField(max_length=3000)
    totalCost = models.FloatField()
    call = models.CharField(max_length=100)
    fundingScheme = models.CharField(max_length=100)


class Organisation(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=250)
    shortName = models.CharField(max_length=100)
    activityType = models.CharField(max_length=3)
    country = models.CharField(max_length=2)
    street = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    postCode = models.CharField(max_length=7, null=True, blank=True)
    regionCode = models.ForeignKey(Region, blank=True, null=True)
    organizationUrl = models.URLField()


class ProjectOrganisation(models.Model):
    class Meta:
        unique_together = (("project", "organisation"),)
    project = models.ForeignKey(Project)
    organisation = models.ForeignKey(Organisation)
    role = models.CharField(max_length=15)
    endOfParticipation = models.BooleanField()
    ecContribution = models.FloatField(default=0)


class ProjectTopics(models.Model):
    project = models.ForeignKey(Project)
    typeGroup = models.CharField(max_length=50, null=True, blank=True)
    type = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    importance = models.FloatField(null=True, blank=True)
    relevance = models.FloatField(null=True, blank=True)
    confidenceLevel = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name


class Industry(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class ProjectIndustry(models.Model):
    project = models.ForeignKey(Project)
    industry = models.ForeignKey(Industry)
    relevance = models.FloatField(default=0)


class Bookmark(models.Model):
    class Meta:
        unique_together = (("user", "project"),)
    user = models.EmailField()
    project = models.ForeignKey(Project)


class Notification(models.Model):
    project = models.ForeignKey(Project)
    message = models.CharField(max_length=140)
    created = models.DateTimeField(auto_now_add=True)
