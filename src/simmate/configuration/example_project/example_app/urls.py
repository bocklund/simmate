"""
Want to make a website interface for your app? Then you'll need to fill this file
out! If you ever venture to this level, we strongly recommend you go through the
django tutorials first: https://docs.djangoproject.com/en/3.2/
"""

from django.urls import path

from .views import example_view, ExampleRelaxationViewSet

urlpatterns = [
    path(
        route="",
        view=example_view,
        name="example_app",
    ),
    path(
        route="example-relaxation/",
        view=ExampleRelaxationViewSet.list_view,
        name="example-list",
    ),
    path(
        route="example-relaxation/<int:pk>/",
        view=ExampleRelaxationViewSet.retrieve_view,
        name="example-retrieve",
    ),
]
