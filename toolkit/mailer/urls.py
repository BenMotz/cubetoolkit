from django.urls import path
from .views import job_cancel, jobs_list, jobs_table

app_name = "mailer"

urlpatterns = [
    # Try to cancel a job
    path("job/<int:job_id>/delete/", job_cancel, name="job-delete"),
    # View all jobs
    path("jobs/", jobs_list, name="jobs-list"),
    # Retrieve job table fragment
    path("job-table/", jobs_table, name="jobs-table"),
]
