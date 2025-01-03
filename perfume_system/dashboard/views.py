from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import F, Count, Sum
from accounts.models import Role
from .models import (
    Formulation, 
    Ingredient, 
    ComplianceIssue, 
    FormulationIngredient, 
    ComplianceRule, 
    QATestResult
)
from django.contrib import messages
from decimal import Decimal, InvalidOperation
import plotly.graph_objects as go
from django.http import HttpResponse
import csv
from datetime import timedelta

# Base Dashboard Views
@login_required
def dashboard_view(request):
    # Check if user has manager role
    user_roles = request.user.roles.all()
    if not user_roles.filter(name='manager').exists():
        return redirect('dashboard:formulations')
    
    # Basic Stats
    total_formulations = Formulation.objects.count()
    compliance_issues_count = ComplianceIssue.objects.filter(status='open').count()
    approved_formulations = Formulation.objects.filter(status='approved').count()
    pending_qa = Formulation.objects.filter(status='pending_qa').count()
    
    # Compliance Distribution for Pie Chart
    compliance_fig = go.Figure(data=[
        go.Pie(
            labels=['Compliant', 'Non-Compliant', 'Pending'],
            values=[
                Formulation.objects.filter(compliance_status='compliant').count(),
                Formulation.objects.filter(compliance_status='non_compliant').count(),
                Formulation.objects.filter(compliance_status='pending').count()
            ],
            hole=.3,
            marker_colors=['#22c55e', '#ef4444', '#f59e0b'],  # Green, Red, Yellow
            textinfo='percent+label'
        )
    ])
    
    compliance_fig.update_layout(
        showlegend=True,
        margin=dict(t=0, b=0, l=0, r=0),
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # Stock Levels Bar Chart with Thresholds
    ingredients = Ingredient.objects.all()
    stock_fig = go.Figure()
    
    # Add current stock bars
    stock_fig.add_trace(go.Bar(
        name='Current Stock',
        x=[ing.name for ing in ingredients],
        y=[float(ing.current_stock) for ing in ingredients],
        marker_color='#3b82f6'  # Blue
    ))

    # Add threshold line
    stock_fig.add_trace(go.Scatter(
        name='Reorder Threshold',
        x=[ing.name for ing in ingredients],
        y=[float(ing.reorder_threshold) for ing in ingredients],
        mode='lines',
        line=dict(color='#ef4444', width=2, dash='dash')  # Red dashed line
    ))

    stock_fig.update_layout(
        barmode='group',
        margin=dict(t=0, b=0, l=0, r=0),
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            gridcolor='rgba(0,0,0,0.1)',
            zerolinecolor='rgba(0,0,0,0.2)'
        ),
        showlegend=True
    )
    
    # Additional Stats
    recent_formulations = Formulation.objects.all()[:5]
    low_stock_count = Ingredient.objects.filter(current_stock__lte=F('reorder_threshold')).count()

    context = {
        # Main Stats
        'total_formulations': total_formulations,
        'compliance_issues_count': compliance_issues_count,
        'approved_formulations': approved_formulations,
        'pending_qa': pending_qa,
        
        # Charts
        'compliance_chart': compliance_fig.to_html(
            full_html=False,
            config={'displayModeBar': False}
        ),
        'stock_chart': stock_fig.to_html(
            full_html=False,
            config={'displayModeBar': False}
        ),
        
        # Additional Stats
        'recent_formulations': recent_formulations,
        'low_stock_count': low_stock_count,
        'total_ingredients': Ingredient.objects.count(),
        'open_issues': ComplianceIssue.objects.filter(status='open')[:5],
    }
    
    return render(request, 'dashboard/dashboard.html', context)
# Formulation Views
@login_required
def formulations_view(request):
    user_roles = request.user.roles.all()
    if not user_roles.filter(name__in=['rd', 'qa']).exists():
        return redirect('dashboard:dashboard')
    
    formulations = Formulation.objects.all().order_by('-created_at')
    return render(request, 'dashboard/formulations/list.html', {
        'formulations': formulations
    })

@login_required
def formulation_detail_view(request, pk):
    user_roles = request.user.roles.all()
    if not user_roles.filter(name__in=['rd', 'qa']).exists():
        return redirect('dashboard:dashboard')
    
    formulation = get_object_or_404(Formulation, pk=pk)
    compliance_issues = ComplianceIssue.objects.filter(formulation=formulation)
    return render(request, 'dashboard/formulations/detail.html', {
        'formulation': formulation,
        'compliance_issues': compliance_issues,
    })

@login_required
def formulation_create_view(request):
    if not request.user.roles.filter(name='rd').exists():
        return redirect('dashboard:formulations')
    
    if request.method == 'POST':
        try:
            # Create formulation
            formulation = Formulation.objects.create(
                name=request.POST['name'],
                                version=request.POST['version'],
                created_by=request.user
            )

            # Get ingredients and quantities
            ingredient_ids = request.POST.getlist('ingredient_ids[]')
            ingredient_quantities = request.POST.getlist('ingredient_quantities[]')

            # Validate at least one ingredient
            if not ingredient_ids or not ingredient_quantities:
                messages.error(request, 'At least one ingredient is required')
                formulation.delete()
                available_ingredients = Ingredient.objects.all()
                return render(request, 'dashboard/formulations/form.html', {
                    'available_ingredients': available_ingredients
                })

            # Process ingredients and update stock
            for id, quantity in zip(ingredient_ids, ingredient_quantities):
                if id and quantity:
                    ingredient = get_object_or_404(Ingredient, pk=id)
                    quantity_decimal = Decimal(str(quantity))

                    # Check stock
                    if quantity_decimal > ingredient.current_stock:
                        messages.error(request, f'Not enough stock for {ingredient.name}. Available: {ingredient.current_stock}')
                        formulation.delete()
                        return redirect('dashboard:formulations')

                    # Create ingredient relationship
                    FormulationIngredient.objects.create(
                        formulation=formulation,
                        ingredient=ingredient,
                        quantity=quantity_decimal
                    )

                    # Update inventory stock
                    ingredient.current_stock -= quantity_decimal
                    ingredient.save()

            # Check compliance
            formulation.check_compliance()

            messages.success(request, 'Formulation created successfully!')
            return redirect('dashboard:formulation_detail', pk=formulation.pk)
        except Exception as e:
            messages.error(request, f'Error creating formulation: {str(e)}')
            if 'formulation' in locals():
                formulation.delete()

    available_ingredients = Ingredient.objects.all()
    return render(request, 'dashboard/formulations/form.html', {
        'available_ingredients': available_ingredients
    })

@login_required
def formulation_edit_view(request, pk):
    if not request.user.roles.filter(name='rd').exists():
        return redirect('dashboard:formulations')
    
    formulation = get_object_or_404(Formulation, pk=pk)
    
    if request.method == 'POST':
        try:
            # Store old ingredients and quantities to restore stock if needed
            old_ingredients = {fi.ingredient: fi.quantity for fi in formulation.formulation_ingredients.all()}
            
            formulation.name = request.POST['name']
            formulation.version = request.POST['version']
            formulation.save()
            
            # First restore old stock
            for ingredient, quantity in old_ingredients.items():
                ingredient.current_stock += quantity
                ingredient.save()
            
            # Delete existing ingredients
            formulation.formulation_ingredients.all().delete()
            
            # Add new ingredients and update stock
            ingredient_ids = request.POST.getlist('ingredient_ids[]')
            ingredient_quantities = request.POST.getlist('ingredient_quantities[]')
            
            for id, quantity in zip(ingredient_ids, ingredient_quantities):
                if id and quantity:
                    try:
                        ingredient = get_object_or_404(Ingredient, pk=id)
                        quantity_decimal = Decimal(str(quantity))
                        
                        # Check if quantity is within stock limits
                        if quantity_decimal > ingredient.current_stock:
                            # Restore previous state
                            for ing, qty in old_ingredients.items():
                                ing.current_stock -= qty
                                ing.save()
                            
                            messages.error(request, f'Not enough stock for {ingredient.name}. Available: {ingredient.current_stock}')
                            return render(request, 'dashboard/formulations/form.html', {
                                'formulation': formulation,
                                'available_ingredients': Ingredient.objects.all()
                            })
                        
                        # Create formulation ingredient and update stock
                        FormulationIngredient.objects.create(
                            formulation=formulation,
                            ingredient=ingredient,
                            quantity=quantity_decimal
                        )
                        
                        # Update the ingredient stock
                        ingredient.current_stock -= quantity_decimal
                        ingredient.save()
                        
                    except Exception as e:
                        # Restore previous state on error
                        for ing, qty in old_ingredients.items():
                            ing.current_stock -= qty
                            ing.save()
                        raise e
            
            # Re-check compliance after editing ingredients
            if formulation.check_compliance():
                messages.success(request, 'Formulation updated and is compliant.')
            else:
                messages.warning(request, 'Formulation updated but has compliance issues. Please review.')
            
            return redirect('dashboard:formulation_detail', pk=formulation.pk)
            
        except Exception as e:
            messages.error(request, f'Error updating formulation: {str(e)}')
    
    available_ingredients = Ingredient.objects.all()
    return render(request, 'dashboard/formulations/form.html', {
        'formulation': formulation,
        'available_ingredients': available_ingredients
    })

@login_required
def formulation_submit_qa(request, pk):
    if not request.user.roles.filter(name='rd').exists():
        messages.error(request, "You are not authorized to submit formulations for QA.")
        return redirect('dashboard:formulations')

    formulation = get_object_or_404(Formulation, pk=pk)
    formulation.status = 'pending_qa'
    formulation.save()
    messages.success(request, "Formulation submitted for QA approval.")
    return redirect('dashboard:formulation_detail', pk=pk)

# Inventory Views
@login_required
def inventory_list_view(request):
    if not request.user.roles.filter(name__in=['rd', 'manager']).exists():
        return redirect('dashboard:dashboard')
    
    ingredients = Ingredient.objects.all().order_by('name')
    return render(request, 'dashboard/inventory/list.html', {
        'ingredients': ingredients
    })

@login_required
def inventory_create_view(request):
    if not request.user.roles.filter(name='rd').exists():
        return redirect('dashboard:inventory')
    
    if request.method == 'POST':
        try:
            ingredient = Ingredient.objects.create(
                name=request.POST['name'],
                current_stock=Decimal(request.POST['current_stock']),
                reorder_threshold=Decimal(request.POST['reorder_threshold'])
            )
            messages.success(request, 'Ingredient added successfully.')
            return redirect('dashboard:inventory')
        except Exception as e:
            messages.error(request, f'Error adding ingredient: {str(e)}')
    
    return render(request, 'dashboard/inventory/form.html')

@login_required
def inventory_edit_view(request, pk):
    if not request.user.roles.filter(name='rd').exists():
        return redirect('dashboard:inventory')
    
    ingredient = get_object_or_404(Ingredient, pk=pk)
    
    if request.method == 'POST':
        try:
            ingredient.name = request.POST['name']
            ingredient.current_stock = Decimal(request.POST['current_stock'])
            ingredient.reorder_threshold = Decimal(request.POST['reorder_threshold'])
            ingredient.save()
            messages.success(request, 'Ingredient updated successfully.')
            return redirect('dashboard:inventory')
        except Exception as e:
            messages.error(request, f'Error updating ingredient: {str(e)}')
    
    return render(request, 'dashboard/inventory/form.html', {
        'ingredient': ingredient
    })

@login_required
def inventory_update_view(request, pk):
    if not request.user.roles.filter(name='rd').exists():
        return redirect('dashboard:inventory')
    
    ingredient = get_object_or_404(Ingredient, pk=pk)
    
    if request.method == 'POST':
        try:
            new_stock = Decimal(request.POST['current_stock'])
            ingredient.current_stock = new_stock
            ingredient.save()
            messages.success(request, f'Stock updated for {ingredient.name}')
            return redirect('dashboard:inventory')
        except Exception as e:
            messages.error(request, f'Error updating stock: {str(e)}')
    
    return render(request, 'dashboard/inventory/update_stock.html', {
        'ingredient': ingredient
    })

@login_required
def inventory_summary_view(request):
    if not request.user.roles.filter(name='manager').exists():
        return redirect('dashboard:dashboard')
    
    ingredients = Ingredient.objects.all().order_by('name')
    low_stock_ingredients = [i for i in ingredients if i.status == 'low_stock']
    
    return render(request, 'dashboard/inventory-summary/inventory-summary.html', {
        'ingredients': ingredients,
        'low_stock_ingredients': low_stock_ingredients
    })

# Compliance Views
@login_required
def compliance_list_view(request):
    if not request.user.roles.filter(name__in=['rd', 'qa']).exists():
        return redirect('dashboard:dashboard')
    
    compliance_issues = ComplianceIssue.objects.all().order_by('-created_at')
    return render(request, 'dashboard/compliance/list.html', {
        'compliance_issues': compliance_issues
    })

@login_required
def compliance_fix_view(request, pk):
    if not request.user.roles.filter(name='rd').exists():
        return redirect('dashboard:compliance')
    
    issue = get_object_or_404(ComplianceIssue, pk=pk)
    
    if request.method == 'POST':
        try:
            action = request.POST.get('action')
            if action == 'mark_in_progress':
                issue.status = 'in_progress'
            elif action == 'mark_resolved':
                issue.status = 'resolved'
            issue.save()
            
            messages.success(request, f'Compliance issue status updated to {issue.get_status_display()}')
            return redirect('dashboard:compliance')
        except Exception as e:
            messages.error(request, f'Error updating compliance issue: {str(e)}')
    
    return render(request, 'dashboard/compliance/fix.html', {
        'issue': issue
    })

# QA View
@login_required
def qa_dashboard_view(request):
    if not request.user.roles.filter(name='qa').exists():
        messages.error(request, "You are not authorized to access the QA Dashboard.")
        return redirect('dashboard:dashboard')

    formulations = Formulation.objects.filter(status='pending_qa')
    return render(request, 'dashboard/qa/dashboard.html', {'formulations': formulations})

@login_required
def qa_approve_view(request, pk):
    if not request.user.roles.filter(name='qa').exists():
        messages.error(request, "You are not authorized to approve formulations.")
        return redirect('dashboard:dashboard')

    formulation = get_object_or_404(Formulation, pk=pk)
    formulation.status = 'approved'
    formulation.save()
    messages.success(request, "Formulation approved successfully.")
    return redirect('dashboard:qa_dashboard')


@login_required
def qa_reject_view(request, pk):
    if not request.user.roles.filter(name='qa').exists():
        messages.error(request, "You are not authorized to reject formulations.")
        return redirect('dashboard:dashboard')

    formulation = get_object_or_404(Formulation, pk=pk)
    formulation.status = 'rejected'
    formulation.save()
    messages.success(request, "Formulation rejected successfully.")
    return redirect('dashboard:qa_dashboard')

@login_required
def qa_test_result_view(request, pk):
    if not request.user.roles.filter(name='qa').exists():
        return redirect('dashboard:dashboard')
    
    formulation = get_object_or_404(Formulation, pk=pk)
    
    if request.method == 'POST':
        try:
            # Create QA test result
            test_result = QATestResult.objects.create(
                formulation=formulation,
                stability_test=request.POST.get('stability_test'),
                performance_test=request.POST.get('performance_test'),
                comments=request.POST.get('comments'),
                tested_by=request.user,
                status=request.POST.get('action')  # 'approve' or 'reject'
            )
            
            # Update formulation status
            formulation.status = 'approved' if request.POST.get('action') == 'approve' else 'rejected'
            formulation.save()
            
            # Show success message
            action_text = 'approved' if request.POST.get('action') == 'approve' else 'rejected'
            messages.success(request, f'Formulation has been {action_text}.')
            
            return redirect('dashboard:qa_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error processing QA test result: {str(e)}')
    
    # Get existing test result if any
    try:
        test_result = QATestResult.objects.get(formulation=formulation)
    except QATestResult.DoesNotExist:
        test_result = None
    
    return render(request, 'dashboard/qa/test_result.html', {
        'formulation': formulation,
        'test_result': test_result
    })


# Reports View
@login_required
def reports_view(request):
    if not request.user.roles.filter(name='manager').exists():
        return redirect('dashboard:dashboard')

    # Formulation Status Counts
    draft_count = Formulation.objects.filter(status='draft').count()
    pending_count = Formulation.objects.filter(status='pending_qa').count()
    approved_count = Formulation.objects.filter(status='approved').count()
    rejected_count = Formulation.objects.filter(status='rejected').count()

    # Formulation Trend Chart (last 6 months)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=180)
    
    # Get all formulations in date range
    formulations = (
        Formulation.objects
        .filter(created_at__range=(start_date, end_date))
        .values('created_at__year', 'created_at__month')
        .annotate(count=Count('id'))
        .order_by('created_at__year', 'created_at__month')
    )

    # Process the dates for the chart
    months = []
    counts = []
    for f in formulations:
        month_date = f"{f['created_at__year']}-{f['created_at__month']:02d}"
        months.append(month_date)
        counts.append(f['count'])

    # Create Trend Chart
    trend_fig = go.Figure()
    trend_fig.add_trace(go.Scatter(
        x=months,
        y=counts,
        mode='lines+markers',
        name='Formulations',
        line=dict(color='#8b5cf6', width=3),
        marker=dict(size=8)
    ))
    
    trend_fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        height=250,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)'),
        showlegend=False
    )

    # Ingredient Usage Chart
    top_ingredients = (
        FormulationIngredient.objects
        .values('ingredient__name')
        .annotate(total_usage=Sum('quantity'))
        .order_by('-total_usage')[:10]
    )

    usage_fig = go.Figure()
    usage_fig.add_trace(go.Bar(
        x=[i['ingredient__name'] for i in top_ingredients],
        y=[float(i['total_usage']) for i in top_ingredients],
        marker_color='#3b82f6'
    ))
    
    usage_fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        height=250,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)'),
        showlegend=False
    )

    context = {
        'draft_count': draft_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'formulation_trend_chart': trend_fig.to_html(full_html=False, config={'displayModeBar': False}),
        'ingredient_usage_chart': usage_fig.to_html(full_html=False, config={'displayModeBar': False}),
        'total_ingredients': Ingredient.objects.count(),
        'low_stock_count': Ingredient.objects.filter(current_stock__lte=F('reorder_threshold')).count(),
        'recent_formulations': Formulation.objects.all().select_related('created_by')[:10],
    }
    
    return render(request, 'dashboard/reports.html', context)

@login_required
def download_formulation_report(request):
    if not request.user.roles.filter(name='manager').exists():
        return redirect('dashboard:dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="formulation_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Version', 'Status', 'Compliance Status', 'Created By', 'Created At'])
    
    formulations = Formulation.objects.all().select_related('created_by')
    for formulation in formulations:
        writer.writerow([
            formulation.name,
            formulation.version,
            formulation.get_status_display(),
            formulation.get_compliance_status_display(),
            formulation.created_by.username,
            formulation.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response

@login_required
def download_ingredient_report(request):
    if not request.user.roles.filter(name='manager').exists():
        return redirect('dashboard:dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ingredient_usage_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Ingredient', 'Current Stock', 'Reorder Threshold', 'Total Usage', 'Status'])
    
    ingredients = Ingredient.objects.annotate(
        total_usage=Sum('formulationingredient__quantity')
    )
    
    for ingredient in ingredients:
        writer.writerow([
            ingredient.name,
            ingredient.current_stock,
            ingredient.reorder_threshold,
            ingredient.total_usage or 0,
            ingredient.status
        ])
    
    return response

# Error Handler
def handler403(request, exception):
    return render(request, 'dashboard/403.html', status=403)