from django.urls import path
from . import views

urlpatterns = [
    path("universe/", views.get_universe, name="get_universe"),
    path("route/", views.route_packet, name="route_packet"),
    path("toggle/", views.toggle_node, name="toggle_node"),
]
