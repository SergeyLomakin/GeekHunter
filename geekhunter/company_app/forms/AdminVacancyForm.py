from django import forms

from company_app.models import Vacancy
from .widgets import BigTextarea


class AdminVacancyFrom(forms.ModelForm):
    class Meta:
        model = Vacancy
        widgets = {
            'description': BigTextarea,
            'error_text': BigTextarea
        }
        fields = '__all__'
