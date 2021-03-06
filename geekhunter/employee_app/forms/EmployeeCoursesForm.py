from django import forms
from django.forms import formset_factory

from employee_app.models import Courses


class EmployeeCoursesForm(forms.ModelForm):
    class Meta:
        model = Courses
        exclude = ['resume']


CousesFormSet = formset_factory(EmployeeCoursesForm, extra=0)
