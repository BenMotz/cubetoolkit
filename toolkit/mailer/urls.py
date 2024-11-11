from django.urls import path, re_path
from .views import job_create, job_cancel, jobs_list

urlpatterns = [
    # Create a mailout job
    path("job/", job_create, name="job-create"),
    # Try to cancel a job
    path("job/<int:job_id>/delete/", job_cancel, name="job-delete"),
    # View all jobs
    path("jobs/", jobs_list, name="jobs-list"),
]
