from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError

class Formulation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_qa', 'Pending QA'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    
    COMPLIANCE_STATUS = [
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('pending', 'Pending Check')
    ]

    name = models.CharField(max_length=200)
    version = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    compliance_status = models.CharField(max_length=20, choices=COMPLIANCE_STATUS, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    ingredients = models.ManyToManyField('Ingredient', through='FormulationIngredient')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - v{self.version}"

    def check_compliance(self):
        """Check compliance after all ingredients are added."""
        has_issues = False

        # Ensure the instance is saved before processing compliance
        if not self.pk:
            raise ValueError("Formulation instance must be saved before checking compliance.")

        for formulation_ingredient in self.formulation_ingredients.all():
            compliant, message = formulation_ingredient.check_compliance()
            if not compliant:
                has_issues = True
                ComplianceIssue.objects.get_or_create(
                    formulation=self,
                    ingredient=formulation_ingredient.ingredient,
                    description=message,
                    defaults={'status': 'open'}
                )
        
        self.compliance_status = 'non_compliant' if has_issues else 'compliant'
        self.save(update_fields=['compliance_status'])
        return not has_issues

    def save_and_update_stock(self):
        """Save the formulation and update ingredient stock."""
        if not self.pk:
            raise ValueError("Formulation instance must be saved before updating stock.")

        try:
            # Check if all ingredients have enough stock
            for formulation_ingredient in self.formulation_ingredients.all():
                ingredient = formulation_ingredient.ingredient
                if ingredient.current_stock < formulation_ingredient.quantity:
                    raise ValidationError(
                        f'Not enough stock for {ingredient.name}. '
                        f'Required: {formulation_ingredient.quantity}, '
                        f'Available: {ingredient.current_stock}'
                    )

            # If we have enough stock, update the quantities
            for formulation_ingredient in self.formulation_ingredients.all():
                ingredient = formulation_ingredient.ingredient
                ingredient.current_stock -= formulation_ingredient.quantity
                ingredient.save()

            # Save the formulation
            super().save()
            return True

        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(f'Error updating stock: {str(e)}')

    def restore_stock(self):
        """Restore stock when a formulation is deleted or updated."""
        if not self.pk:
            raise ValueError("Formulation instance must be saved before restoring stock.")

        try:
            for formulation_ingredient in self.formulation_ingredients.all():
                ingredient = formulation_ingredient.ingredient
                ingredient.current_stock += formulation_ingredient.quantity
                ingredient.save()
        except Exception as e:
            raise ValidationError(f'Error restoring stock: {str(e)}')

    def save(self, *args, **kwargs):
        """Ensure the formulation is valid before saving."""
        super().save(*args, **kwargs)  # Save instance to assign primary key

class Ingredient(models.Model):
    name = models.CharField(max_length=200, unique=True)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dashboard_ingredient'  # Explicitly set table name

    @property
    def status(self):
        if self.current_stock <= self.reorder_threshold:
            return 'low_stock'
        return 'in_stock'

    def __str__(self):
        return self.name

class FormulationIngredient(models.Model):
    formulation = models.ForeignKey(Formulation, related_name='formulation_ingredients', on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.ingredient.name} ({self.quantity})"

    def check_compliance(self):
        try:
            rule = ComplianceRule.objects.get(ingredient=self.ingredient)
            if self.quantity > rule.max_quantity:
                return False, f"Quantity exceeds maximum allowed ({rule.max_quantity})"
            return True, "Compliant"
        except ComplianceRule.DoesNotExist:
            return True, "No rules defined"

class ComplianceRule(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    max_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rule for {self.ingredient.name}"

class ComplianceIssue(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved')
    ]

    formulation = models.ForeignKey(Formulation, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Compliance Issue: {self.formulation.name} - {self.ingredient.name}"
    
class QATestResult(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    formulation = models.ForeignKey(Formulation, on_delete=models.CASCADE, related_name='qa_results')
    stability_test = models.TextField(null=True, blank=True)
    performance_test = models.TextField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    tested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    tested_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['-tested_at']

    def save(self, *args, **kwargs):
        # Update formulation status when QA result is saved
        if self.status in ['approved', 'rejected']:
            self.formulation.status = self.status
            self.formulation.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"QA Result for {self.formulation} - {self.get_status_display()}"