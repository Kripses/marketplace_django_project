"""
URL configuration for megano project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an product_import:  from my_app product_import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an product_import:  from other_app.views product_import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls product_import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.i18n import i18n_patterns

from products.views import IndexView


urlpatterns = [
    path("admin/", admin.site.urls),
    path('payment/', include('payments.urls')),
]

urlpatterns += i18n_patterns(
    path('account/', include('account.urls')),
    path('sale/', include('discounts.urls')),
    path('cart/', include('cart.urls')),
    path('catalog/', include('products.urls')),
    path('', IndexView.as_view(), name='index'),
)

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
    urlpatterns.extend(
        static(
            settings.STATIC_URL,
            document_root=settings.STATIC_ROOT
        )
    )
    urlpatterns.append(
        path("__debug__/", include("debug_toolbar.urls")),
    )
