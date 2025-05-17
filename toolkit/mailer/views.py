from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import permission_required
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render

from .forms import JobForm
from .models import MailoutJob


@permission_required("toolkit.write")
@require_POST
def job_create(request: HttpRequest) -> HttpResponse:
    job_form = JobForm(request.POST)
    if job_form.is_valid():
        job = job_form.save()
        return HttpResponse(f"<p>Created job {job.pk}</p>")
    else:
        return HttpResponse("No")


@permission_required("toolkit.write")
@require_POST
def job_cancel(request: HttpRequest, job_id: int) -> HttpResponse:
    job = get_object_or_404(MailoutJob, pk=job_id)
    job.do_cancel()
    job.save()
    return HttpResponseRedirect(reverse("mailer:jobs-list"))


@permission_required("toolkit.read")
def jobs_list(request) -> HttpResponse:
    show_completed = request.GET.get("show-completed") == "true"
    show_failed = request.GET.get("show-failed", "true") == "true"

    jobs = MailoutJob.objects.all().order_by("-id")

    if not show_completed:
        jobs = jobs.exclude(
            state__in=(
                MailoutJob.SendState.SENT,
                MailoutJob.SendState.CANCELLED,
            )
        )
        if not show_failed:
            jobs = jobs.exclude(state=MailoutJob.SendState.FAILED)

    return render(
        request,
        "jobs-list.html",
        context={
            "jobs": jobs,
            "show_completed": show_completed,
            "show_failed": show_failed,
        },
    )
