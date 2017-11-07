from django.conf.urls import url
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    url(r'^login/$', LoginView.as_view(template_name='login.html'),
        name='login'),
    url(r'^logout/$', LogoutView.as_view(template_name='logout.html'),
        name='logout'),
]
