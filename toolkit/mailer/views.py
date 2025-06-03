from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import permission_required
from django.urls import reverse
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import get_object_or_404, render

from .models import MailoutJob


@permission_required("toolkit.write")
@require_POST
def job_cancel(request: HttpRequest, job_id: int) -> HttpResponse:
    job = get_object_or_404(MailoutJob, pk=job_id)
    job.do_cancel()
    job.save()
    return HttpResponseRedirect(reverse("mailer:jobs-list"))


def _query_jobs(show_completed: bool, show_failed: bool):
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

    return jobs


@permission_required("toolkit.read")
@require_GET
def jobs_list(request: HttpRequest) -> HttpResponse:
    show_completed = False
    show_failed = True
    jobs = _query_jobs(show_completed=show_completed, show_failed=show_failed)

    poll_for_updates = any(
        job.state
        in (
            MailoutJob.SendState.PENDING,
            MailoutJob.SendState.SENDING,
            MailoutJob.SendState.CANCELLING,
        )
        for job in jobs
    )

    return render(
        request,
        "jobs-list.html",
        context={
            "jobs": jobs,
            "poll_for_updates": poll_for_updates,
            "show_completed": show_completed,
            "show_failed": show_failed,
        },
    )


@permission_required("toolkit.read")
@require_GET
def jobs_table(request: HttpRequest) -> HttpResponse:
    show_completed = request.GET.get("show-completed") == "on"
    show_failed = request.GET.get("show-failed", "true") == "on"
    poll_for_updates = request.GET.get("poll-for-updates") == "on"

    jobs = _query_jobs(show_completed=show_completed, show_failed=show_failed)

    return render(
        request,
        "jobs-list-table.html",
        context={
            "jobs": jobs,
            "poll_for_updates": poll_for_updates,
            "show_completed": show_completed,
            "show_failed": show_failed,
        },
    )
