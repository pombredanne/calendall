import logging

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import CreateView, FormView, RedirectView

from .models import CalendallUser
from .forms import CalendallUserCreateForm, LoginForm

from core import utils

log = logging.getLogger(__name__)


class CalendallUserCreate(CreateView):
    model = CalendallUser
    fields = ['username', 'email', 'password']
    form_class = CalendallUserCreateForm
    template_name = "profiles/profiles_calendalluser_create.html"
    success_url = reverse_lazy('profiles:calendalluser_create')

    def get_success_url(self):
        # Auto log in process:
        # Check password & user is ok (this isn't neccesary)
        user = authenticate(username=self.request.POST['username'],
                            password=self.request.POST['password'])
        if user is not None:
            if user.is_active:
                log.debug("Auto login '{0}'".format(user))
                login(self.request, user)

        # Send welcome email
        utils.send_templated_email("profiles/emails/profiles_email_welcome",
                                   self.get_context_data(),
                                   _("Welcome to Calendall"),
                                   settings.EMAIL_SUPPORT,
                                   (user.email,),
                                   self.request)

        return self.success_url

    @method_decorator(sensitive_post_parameters('password',
                                                'password_verification'))
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class Login(FormView):

    form_class = LoginForm
    template_name = "profiles/profiles_login.html"
    success_url = settings.LOGIN_REDIRECT_URL

    def form_valid(self, form):
        login(self.request, form.get_user())
        if self.request.session.test_cookie_worked():
            self.request.session.delete_test_cookie()
        return super().form_valid(form)

    def get_success_url(self):
        # First check POST
        next_url = self.request.POST.get('next', None)

        if not next_url:
            next_url = self.request.GET.get('next', None)

        if next_url:
            self.success_url = next_url

        return self.success_url

    @method_decorator(sensitive_post_parameters('password'))
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        request.session.set_test_cookie()
        return super().dispatch(request, *args, **kwargs)


class Logout(RedirectView):

    url = settings.LOGIN_REDIRECT_URL

    def get(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, _("successfuly logged out"))
        return super().get(request, *args, **kwargs)
