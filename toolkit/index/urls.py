from django.conf.urls import url
import django.utils.functional as functional
import django.views.generic.edit as generic_edit
from django.contrib.auth.decorators import permission_required
from django.urls import reverse

from toolkit.index.models import IndexLink, IndexCategory

write_decorator = permission_required('toolkit.write')

urlpatterns = [
    # Link edit:
    url(r'^create/link$',
        write_decorator(generic_edit.CreateView.as_view(
            model=IndexLink,
            fields=('text', 'link', 'category'),
            template_name="index_generic_form.html",
            # Need to use 'lazy', as 'reverse' won't work until urlpatterns
            # (this data structure) has been defined.
            success_url=functional.lazy(reverse, str)("toolkit-index"),
        )),
        name='create-index-link'),
    url(r'^update/link/(?P<pk>\d+)$',
        write_decorator(generic_edit.UpdateView.as_view(
            model=IndexLink,
            template_name="index_generic_form.html",
            fields=('text', 'link', 'category'),
            success_url=functional.lazy(reverse, str)("toolkit-index"),
        )),
        name='update-index-link'),
    url(r'^delete/link/(?P<pk>\d+)$',
        write_decorator(generic_edit.DeleteView.as_view(
            model=IndexLink,
            template_name="index_delete_form.html",
            success_url=functional.lazy(reverse, str)("toolkit-index"),
        )),
        name='delete-index-link'),
    # Category edit:
    url(r'^create/category$',
        write_decorator(generic_edit.CreateView.as_view(
            model=IndexCategory,
            fields=('name',),
            template_name="index_generic_form.html",
            success_url=functional.lazy(reverse, str)("toolkit-index"),
        )),
        name='create-index-category'),
    url(r'^update/category/(?P<pk>\d+)$',
        write_decorator(generic_edit.UpdateView.as_view(
            model=IndexCategory,
            fields=('name',),
            template_name="index_generic_form.html",
            success_url=functional.lazy(reverse, str)("toolkit-index"),
        )),
        name='update-index-category'),
]
