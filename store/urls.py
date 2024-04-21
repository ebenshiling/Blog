from django.urls import path
from . import views



urlpatterns = [
    path('', views.store, name='store'),
    
    # This URL pattern maps a slug to a category, and calls the `store` view
    # with that category object as the keyword argument `category`.
    # The view will show all products that belong to that category.
    path('<slug:category_slug>/',views.store,name='products_by_category'),
    path('<slug:category_slug>/<slug:product_slug>/',views.product_detail,name='product_detail'),

    
]
