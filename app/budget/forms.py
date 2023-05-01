from django import forms
from core.models import Month, Category, SubCategory, Transaction, Account
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError

from .month_year import month_year_choices


class MonthSelectForm(forms.Form):
    """Month Select Form on Budget Dashboard"""
    month_year = forms.ChoiceField(
        choices=month_year_choices,
        widget=forms.RadioSelect(attrs={'onchange': 'submit();'}))


class AccountForm(LoginRequiredMixin, forms.ModelForm):
    """Account Create and Update Form"""
    class Meta:
        model = Account
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'name',
                'placeholder':
                'ex. Chase Bank'
            })
        }


class MonthForm(LoginRequiredMixin, forms.ModelForm):
    """Month Create Form"""
    month_year = forms.ChoiceField(
        choices=month_year_choices,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'month-year',
        })
    )
    copy = forms.BooleanField(
        required=False, 
        widget=forms.RadioSelect(
            choices=(
                (True, 'Yes'), 
                (False, 'No')
            )
        )
    )

    class Meta:
        model = Month
        fields = '__all__'


class CategoryForm(LoginRequiredMixin, forms.ModelForm):
    """Category Create and Update Form"""
    class Meta:
        model = Category
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'name'
            })
        }


class SubCategoryForm(LoginRequiredMixin, forms.ModelForm):
    """Subcategory Create and Update Form"""
    class Meta:
        model = SubCategory
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'name'
            }),
            'amount': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'amount'
            }),
            'type': forms.RadioSelect(attrs={
                'class': 'form-check-input',
                'id': 'type'
            }),
            'fund': forms.RadioSelect(attrs={
                'class': 'form-check-input',
                'id': 'fund'
            })
        }

    def clean(self):
        cleaned_data = super().clean()

        # This prevents a user from creating a savings subcategory that is
        # not a Sinking Fund.
        fund = cleaned_data['fund']
        type = cleaned_data['type']
        if type == 'savings' and fund is False:
            raise ValidationError(
                'Savings Subcategories must be Funds.'
            )


class TransactionForm(LoginRequiredMixin, forms.ModelForm):
    """Transaction Create and Update Form"""
    class Meta:
        model = Transaction
        fields = '__all__'
        widgets = {
            'subcategory': forms.Select(attrs={
                'class': 'form-control',
                'id': 'subcategory'
            }),
            'expense': forms.Select(attrs={
                'class': 'form-control',
                'id': 'expense'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'date'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'amount'
            }),
            'vendor': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'vendor'
            }),
            'account': forms.Select(attrs={
                'class': 'form-control',
                'id': 'account'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'notes',
                'rows': '5'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #######################################
        # This code limits the choices of the subcategory field to those
        # created by the currently logged in user. 'initial' data is
        # passed to the form by the TransactionCreateView class in views.py.
        month = Month.objects.get(
            user=kwargs['initial']['user'],
            month=kwargs['initial']['month'],
            year=kwargs['initial']['year']
        )
        category_ids = [i.id for i in Category.objects.filter(month=month)]
        subcategories = SubCategory.objects.filter(
            category_id__in=category_ids
        )
        # Label format: '[Category name] - [Subcategory name]'
        self.fields['subcategory'].choices = (
            (s.id, f"{Category.objects.get(id=s.category_id)} - {s}")
            for s in subcategories
        )
        self.fields['account'].choices = [
            (account.id, account.name) for account in Account.objects.filter(
                user=kwargs['initial']['user']
            )]
        self.fields['account'].choices.insert(0, ('', ''))
        #######################################
