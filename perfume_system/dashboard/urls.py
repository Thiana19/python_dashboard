from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Formulations URLs
    path('formulations/', views.formulations_view, name='formulations'),
    path('formulations/new/', views.formulation_create_view, name='formulation_create'),
    path('formulations/<int:pk>/', views.formulation_detail_view, name='formulation_detail'),
    path('formulations/<int:pk>/edit/', views.formulation_edit_view, name='formulation_edit'),
    path('formulations/<int:pk>/submit-qa/', views.formulation_submit_qa, name='formulation_submit_qa'),

    # Inventory URLs
    path('inventory/', views.inventory_list_view, name='inventory'),
    path('inventory/new/', views.inventory_create_view, name='inventory_create'),
    path('inventory/<int:pk>/edit/', views.inventory_edit_view, name='inventory_edit'),
    path('inventory/<int:pk>/update/', views.inventory_update_view, name='inventory_update'),
    path('inventory-summary/', views.inventory_summary_view, name='inventory_summary'),

    # Compliance URLs
    path('compliance/', views.compliance_list_view, name='compliance'),
    path('compliance/<int:pk>/fix/', views.compliance_fix_view, name='compliance_fix'),

    # QA URLs
    path('qa-dashboard/', views.qa_dashboard_view, name='qa_dashboard'),
    path('qa/<int:pk>/approve/', views.qa_approve_view, name='qa_approve'),
    path('qa/<int:pk>/reject/', views.qa_reject_view, name='qa_reject'),
    path('qa/test-result/<int:pk>/', views.qa_test_result_view, name='qa_test_result'),
    
    # Reports URL
    path('reports/', views.reports_view, name='reports'),
    path('reports/download/formulations/', views.download_formulation_report, name='download_formulation_report'),
    path('reports/download/ingredients/', views.download_ingredient_report, name='download_ingredient_report'),
]