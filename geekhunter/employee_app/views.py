import json

from django.apps import apps
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core import serializers
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, FormView, DetailView, DeleteView, UpdateView

from company_app.models import FavoriteResume, Offer, HrManager, Vacancy
from employee_app.forms.EmployeeOfferAnswerForm import EmployeeOfferAnswerForm
from employee_app.forms.EmployeeResponseForm import EmployeeResponseForm
from employee_app.forms.EmployeeResumeForm import EmployeeResumeForm
from employee_app.models import Employee, Resume, Experience, Education, Courses, Response


class EmployeeProfileView(View):
    profile = None

    def dispatch(self, request, *args, **kwargs):
        self.profile = Employee.objects.get(user_id=request.user.id)
        return super(EmployeeProfileView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        context = {
            'title': f'профиль {self.profile.user.username}',
            'employee': self.profile,
        }
        return render(request, 'employee_app/employee_profile.html', context)


class EmployeeProfileResumeView(ListView):
    template_name = 'employee_app/profile_resumes.html'
    context_object_name = 'resumes'

    def get_queryset(self):
        return Resume.objects.filter(employee_id=self.request.user.id)


@method_decorator(csrf_exempt, name='dispatch')
class ResumeCreationView(FormView):
    template_name = 'employee_app/resume_create.html'
    form_class = EmployeeResumeForm
    extra_context = {
        'title': 'Создание резюме',
    }
    success_url = reverse_lazy('employee:profile_resumes')

    def get(self, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        employee = Employee.objects.get(user_id=self.request.user.id)
        body_unicode = request.body.decode('utf-8')
        try:
            body = json.loads(body_unicode)
            resume = Resume(
                title=body['title'],
                status=body['status'],
                employee=employee
            )
            resume.save()
            for key in body['fields']:
                for value in body["fields"][key]:
                    model = apps.get_model('employee_app', key.capitalize())(
                        **value,
                        resume=resume
                    )
                    model.save()

        except Exception as e:
            print(e)

        return HttpResponseRedirect(self.success_url)


@method_decorator(csrf_exempt, name='dispatch')
class ResumeEditView(UpdateView):
    template_name = 'employee_app/resume_edit.html'
    model = Resume
    queryset = Resume.objects.all()
    form_class = EmployeeResumeForm
    success_url = reverse_lazy('employee:profile_resumes')

    def get_context_data(self, **kwargs):
        context = super(ResumeEditView, self).get_context_data()
        resume_id = self.get_object().id
        context['title'] = f'Редактирование {self.get_object().title}'

        experiences = Experience.objects.filter(resume_id=resume_id)
        experiences_json = serializers.serialize('python', experiences)

        educations = Education.objects.filter(resume_id=resume_id)
        educations_json = serializers.serialize('python', educations)

        courses = Courses.objects.filter(resume_id=resume_id)
        courses_json = serializers.serialize('python', courses)

        context['experiencies'] = experiences_json
        context['educations'] = educations_json
        context['courses'] = courses_json
        return context

    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        try:
            body = json.loads(body_unicode)
            resume = Resume.objects.get(id=body['pk'])
            resume.title = body['title']
            resume.status = body['status']
            resume.save()
            for key in body['fields']:
                for value in body["fields"][key]:
                    if int(value['pk']) > 0:
                        model = apps.get_model('employee_app', key.capitalize()).objects.get(id=value['pk'])
                        for _key in value:
                            if _key != 'pk':
                                setattr(model, _key, value[_key])
                    else:
                        new_model_credentials = {}
                        for _key in value:
                            if _key != 'pk':
                                new_model_credentials[_key] = value[_key]
                        model = apps.get_model('employee_app', key.capitalize())(
                            **new_model_credentials,
                            resume=resume
                        )

                    model.save()
        except Exception as e:
            print(e)

        return JsonResponse([], safe=False)


class ResumeDetailView(DetailView):
    template_name = 'employee_app/resume_detail.html'
    queryset = Resume.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resume_id = self.get_object().id
        context['title'] = self.get_object().title
        context['experiencies'] = Experience.objects.filter(resume_id=resume_id)
        context['educations'] = Education.objects.filter(resume_id=resume_id)
        context['courses'] = Courses.objects.filter(resume_id=resume_id)
        return context


class ResumeDeleteView(DeleteView):
    model = Resume
    template_name = 'employee_app/resume_delete.html'
    context_object_name = 'resume'
    success_url = reverse_lazy('employee:profile_resumes')


class ResumesView(PermissionRequiredMixin, ListView):
    login_url = 'auth_app:login'
    permission_required = 'employee_app.view_resume'
    template_name = 'employee_app/resumes.html'
    extra_context = {
        'title': 'резюме',
        'favorite_resumes': 'favorite_resumes',
    }

    context_object_name = 'resumes'
    ordering = ['-updated_at']

    def get_queryset(self):
        if 'pk' in self.kwargs:
            return Resume.objects.filter(
                employee_id=self.kwargs.get('pk'),
                status='ACTIVE'
            ).order_by(*self.ordering)
        else:
            return Resume.objects.filter(status='ACTIVE').order_by(*self.ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['favorite_resumes'] = FavoriteResume.objects.filter(hr_manager=self.request.user.id)
        return context

    def post(self, request, *args, **kwargs):
        resume_id = request.POST.get('resume')
        resume = Resume.objects.get(id=resume_id)
        hr_manager = HrManager.objects.get(user_id=self.request.user.id)

        favorite_resume = FavoriteResume.objects.filter(
            resume=resume,
            hr_manager=hr_manager,
        )

        if not favorite_resume:
            favorite_resume = FavoriteResume.objects.create(
                resume=resume,
                hr_manager=hr_manager,
            )
            favorite_resume.save()

        return HttpResponseRedirect(reverse('employee_app:resumes'))


@method_decorator(csrf_exempt, name='dispatch')
class ResumeEntityDeleteView(View):
    @staticmethod
    def post(request):
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            model = apps.get_model('employee_app', body['model'].capitalize()).objects.get(id=body['pk'])
            model.delete()
        except Exception as e:
            print(e)
        return JsonResponse([], safe=False)


@receiver(pre_save, sender=Resume)
def resume_status_change(sender, instance, **kwargs):
    if instance.status == 'ACTIVE':
        for item in Resume.objects.filter(employee=instance.employee).exclude(id=instance.id):
            item.status = 'DRAFT'
            item.save()


class EmployeeOffersView(ListView):
    template_name = 'employee_app/profile_offers.html'
    context_object_name = 'offers'

    def get_queryset(self):
        return Offer.objects.filter(resume__employee=self.request.user.id).filter(status__in=['SENT', 'ACCEPTED'])


class EmployeeOfferAnswerView(FormView):
    template_name = 'employee_app/offer_answer.html'
    form_class = EmployeeOfferAnswerForm
    success_url = reverse_lazy('employee:profile_offers')

    def get_context_data(self, **kwargs):
        context = super(EmployeeOfferAnswerView, self).get_context_data(**kwargs)
        context['offer'] = Offer.objects.get(id=self.kwargs['pk'])
        resume_id = context['offer'].resume.id
        context['resume'] = Resume.objects.get(id=resume_id)
        context['experiencies'] = Experience.objects.filter(resume_id=resume_id)
        context['educations'] = Education.objects.filter(resume_id=resume_id)
        context['courses'] = Courses.objects.filter(resume_id=resume_id)
        return context

    def post(self, request, *args, **kwargs):
        offer = self.get_context_data()['offer']
        offer.feedback = request.POST.get('feedback')
        if 'accept' in request.POST:
            offer.status = 'ACCEPTED'
        else:
            offer.status = 'NOT_ACCEPTED'
        offer.save()

        return HttpResponseRedirect(self.success_url)


class MakeResponseView(FormView):
    form_class = EmployeeResponseForm
    template_name = 'employee_app/make_response.html'
    success_url = reverse_lazy('company:vacancies')

    def get_form_kwargs(self):
        kwargs = super(MakeResponseView, self).get_form_kwargs()
        kwargs['vacancy_id'] = Vacancy.objects.filter(id=self.kwargs['vacancy_id'])
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super(MakeResponseView, self).get_initial()
        initial['vacancy'] = Vacancy.objects.get(id=self.kwargs['vacancy_id'])
        return initial

    def post(self, request, *args, **kwargs):
        response = Response(
            title=request.POST.get('title'),
            text=request.POST.get('text'),
            resume=Resume.objects.get(id=request.POST.get('resume')),
            vacancy=Vacancy.objects.get(id=request.POST.get('vacancy'))
        )
        response.save()

        return HttpResponseRedirect(self.success_url)


class EmployeeResponsesListView(ListView):
    template_name = 'employee_app/profile_responses.html'
    context_object_name = 'responses'

    def get_queryset(self):
        return Response.objects.filter(resume__employee=self.request.user.id)


class ResponseDeleteView(DeleteView):
    model = Offer
    template_name = 'employee_app/response_delete.html'
    context_object_name = 'response'
    success_url = reverse_lazy('employee:profile_responses')
