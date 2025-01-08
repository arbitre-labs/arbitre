from django.urls import re_path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"submission", views.SubmissionViewSet)
router.register(r"test", views.TestViewSet)
router.register(r"tests-raw", views.RawTestsViewSet, basename="tests-raw")
router.register(r"testresult", views.TestResultViewSet, basename="testresult")
router.register(
    r"refresh-submission", views.RefreshSubmissionViewSet, basename="refresh"
)
router.register(
    r"submission-file", views.SubmissionFileViewSet, basename="submission-file"
)
router.register(
    r"requeue-submissions",
    views.RequeueSubmissionsViewSet,
    basename="requeue-submissions",
)

urlpatterns = [
    re_path("api/", include(router.urls)),
    re_path(
        "api/judge0-callback",
        views.Judge0CallbackView.as_view(),
        name="judge0-callback",
    ),
]
