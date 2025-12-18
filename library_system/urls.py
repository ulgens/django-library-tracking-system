from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from library import views
from debug_toolbar.toolbar import debug_toolbar_urls

router = routers.DefaultRouter()
router.register(r'authors', views.AuthorViewSet)
router.register(r'books', views.BookViewSet)
router.register(r'members', views.MemberViewSet)
router.register(r'loans', views.LoanViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
] + debug_toolbar_urls()
