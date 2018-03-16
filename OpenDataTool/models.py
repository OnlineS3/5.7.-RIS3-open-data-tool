# -*- coding:utf-8 -*-

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


class FrameworkProgramme(models.Model):
    id = models.CharField(primary_key=True, max_length=4)
    frameworkProgramme = models.CharField(max_length=50)
    shortName = models.CharField(max_length=5)
    startYear = models.PositiveSmallIntegerField()
    endYear = models.PositiveSmallIntegerField()


@python_2_unicode_compatible
class Region(models.Model):
    order = models.IntegerField()
    level = models.IntegerField()
    code = models.IntegerField(primary_key=True)
    parent = models.ForeignKey("self", blank=True, null=True)
    nutsCode = models.CharField(max_length=6)
    description = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

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
    acronym = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=100)
    programme = models.CharField(max_length=100, blank=True, null=True)
    topics = models.CharField(max_length=100)
    frameworkProgramme = models.CharField(max_length=5)
    title = models.CharField(max_length=250)
    startDate = models.DateField(blank=True, null=True)
    endDate = models.DateField(blank=True, null=True)
    projectUrl = models.URLField(blank=True, null=True)
    objective = models.CharField(max_length=3000, blank=True, null=True)
    totalCost = models.FloatField(blank=True, null=True, default=None)
    call = models.CharField(max_length=100,blank=True, null=True)
    fundingScheme = models.CharField(max_length=100, blank=True, null=True)


class Organisation(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=250)
    shortName = models.CharField(max_length=100, blank=True, null=True)
    activityType = models.CharField(max_length=3)
    country = models.CharField(max_length=2)
    street = models.CharField(max_length=250, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
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


class Topic(models.Model):
    title = models.CharField(max_length=300)
    topicRcn = models.IntegerField(primary_key=True)
    topicCode = models.CharField(max_length=32)
    legalBasisRcn = models.IntegerField(null=True, blank=True)
    legalBasisCode = models.CharField(max_length=32, null=True, blank=True)


class Call(models.Model):
    callIdentifier = models.CharField(max_length=100, primary_key=True)
    active = models.BooleanField()
    title = models.CharField(max_length=300)
    frameworkProgramme = models.CharField(max_length=5)
    programme = models.CharField(max_length=100)
    wpPart = models.CharField(max_length=100)
    publicationDate = models.DateField()


class CallBudget(models.Model):
    call = models.ForeignKey(Call)
    topic = models.CharField(max_length=300)
    budget = models.FloatField()
    year = models.PositiveIntegerField()
    stages = models.CharField(max_length=300)
    openDate = models.DateField()
    deadline = models.DateField()


class OrganisationActivityType(models.Model):
    code = models.CharField(primary_key=True, max_length=3)
    title = models.CharField(max_length=100)


class PostcodeRegion(models.Model):
    code = models.CharField(max_length=7)
    nutsCode = models.CharField(max_length=6)
    country = models.CharField(max_length=2)
