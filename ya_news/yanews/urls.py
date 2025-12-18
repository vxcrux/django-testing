from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import UserCreationForm
from django.urls import include, path, reverse_lazy
from django.views.generic import CreateView

urlpatterns = [
    path("", include("news.urls")),
    path("admin/", admin.site.urls),
]

auth_urls = (
    [
        path(
            "login/",
            auth_views.LoginView.as_view(),
            name="login",
        ),
        path(
            "logout/",
            auth_views.LogoutView.as_view(
                next_page=reverse_lazy("users:login")
            ),
            name="logout",
        ),
        path(
            "signup/",
            CreateView.as_view(
                form_class=UserCreationForm,
                success_url=reverse_lazy("news:home"),
                template_name="registration/signup.html",
            ),
            name="signup",
        ),
    ],
    "users",
)

urlpatterns += [
    path("auth/", include((auth_urls[0], "users")), name="users"),
]
