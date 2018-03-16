from django import forms
from django_select2.forms import ModelSelect2MultipleWidget
from OpenDataTool.models import Region, Organisation, Industry


class SearchForm(forms.Form):
    objective = forms.CharField(
        label="Key term:",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    industry = forms.ModelChoiceField(
        label="Industry:",
        queryset=Industry.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    region = forms.ModelMultipleChoiceField(
        label="Choose regions to include in your search:",
        widget=ModelSelect2MultipleWidget(
            queryset=Region.objects.filter(
                code__in=Organisation.objects.exclude(regionCode__code__isnull=True).values_list('regionCode').distinct()),
            search_fields=['description__icontains'],
            attrs={"class": "form-control", "data-placeholder": "Choose regions"}
        ),
        queryset=Region.objects.all(),
        required=False
    )


class ExploreRegionForm(forms.Form):
    region = forms.ModelMultipleChoiceField(
        label="Choose regions to include in your search:",
        widget=ModelSelect2MultipleWidget(
            queryset=Region.objects.filter(code__in=Organisation.objects.exclude(regionCode__code__isnull=True).values_list('regionCode').distinct()),
            search_fields=['description__icontains'],
            attrs={"class": "form-control", "data-placeholder": "Choose regions"}
        ),
        queryset=Region.objects.all(),
        required=True
    )


class ExploreIndustryForm(forms.Form):
    industries = forms.ModelMultipleChoiceField(
        label="Choose industries to include in your search:",
        widget=ModelSelect2MultipleWidget(
            queryset=Industry.objects.all(),
            search_fields=['name'],
            attrs={"class": "form-control", "data-placeholder": "Choose industry"}
        ),
        queryset=Industry.objects.all(),
        required=True
    )
