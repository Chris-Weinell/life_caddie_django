"""
Budget App URLs.
"""
from django.urls import path
from . import views

app_name = 'budget'

# AccountViews Origin vs. Source - origin is used to route back buttons on
#  Accounts pages.  Source is used to route success urls when new accounts
#  are created from within Transaction Views.
urlpatterns = [
    path('', views.budget_dashboard, name='budget_dashboard'),
    path(
        'month/',
        views.FirstMonthCreateView.as_view(),
        name='first_month'
    ),
    path(
        'new_month/',
        views.NewMonthCreateView.as_view(),
        name='new_month'
    ),
    path(
        'account/<str:source>',
        views.AccountCreateView.as_view(),
        name='account'
    ),
    path(
        'accounts/',
        views.AccountListView.as_view(),
        name='account_list'
    ),
    path(
        'account/<str:origin>/<int:pk>',
        views.AccountUpdateView.as_view(),
        name='update_account'
    ),
    path(
        'delete_account/<str:origin>/<int:pk>',
        views.AccountDeleteView.as_view(),
        name='delete_account'
    ),
    path(
        'category/',
        views.CategoryCreateView.as_view(),
        name='category'
    ),
    path(
        'category/<int:pk>',
        views.CategoryUpdateView.as_view(),
        name='update_category'
    ),
    path(
        'delete_category/<int:pk>',
        views.CategoryDeleteView.as_view(),
        name='delete_category'
    ),
    path(
        'subcategory/<int:category>/',
        views.SubCategoryCreateView.as_view(),
        name='subcategory'
    ),
    path(
        'subcategory/<int:category>/<int:pk>',
        views.SubCategoryUpdateView.as_view(),
        name='update_subcategory'
    ),
    path(
        'delete_subcategory/<int:category>/<int:pk>',
        views.SubCategoryDeleteView.as_view(),
        name='delete_subcategory'
    ),
    path(
        'transaction/',
        views.TransactionCreateView.as_view(),
        name='transaction'
    ),
    path(
        'transaction/<str:source>/<int:subcategory_id>/<int:pk>',
        views.TransactionUpdateView.as_view(),
        name='update_transaction'
    ),
    path(
        'transactions/',
        views.TransactionListView.as_view(),
        name='transaction_list'
    ),
    path(
        'delete_transaction/<str:source>/<int:subcategory_id>/<int:pk>',
        views.TransactionDeleteView.as_view(),
        name='delete_transaction'
    ),
]
