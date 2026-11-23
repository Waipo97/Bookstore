from django.urls import path
from rest_framework.routers import DefaultRouter

from .api import AuthorViewSet, BookPhotoViewSet, BookViewSet, GenreViewSet, OrderViewSet, UserViewSet
from .auth_views import LoginView, LogoutView, MeView, RegisterView

router = DefaultRouter()
router.register("genres", GenreViewSet)
router.register("authors", AuthorViewSet)
router.register("books", BookViewSet)
router.register("book-photos", BookPhotoViewSet)
router.register("orders", OrderViewSet)
router.register("users", UserViewSet)

urlpatterns = [
    path("auth/me/", MeView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("auth/register/", RegisterView.as_view()),
] + router.urls
