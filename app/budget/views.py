from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from core.models import Month, Category, SubCategory, Transaction, Account
from . import forms
from .month_year import month_reference_dict, month_reference_dict_full
from datetime import datetime


def my_reverse(viewname, kwargs=None, additional=None):
    """
    Custom reverse to add a urlconf after the url
    Example usage:
    url = my_reverse('my_test_url', kwargs={'pk': object.id}, additional=data)
    """
    url = reverse(viewname, kwargs=kwargs)

    if additional:
        return f'{url}?vals={additional}'

    return url

def collect_dashboard_table_data(request):
    # This generates data that is displayed on the Cards section of the page.

    # This creates a list of the Categories associated with
    # the logged-in user and the selected month and year.
    categories = Category.objects.filter(
        month=Month.objects.get(
            user=request.user,
            month=request.session['date']['month'],
            year=request.session['date']['year']
        )
    ).order_by('id')

    # This attaches the subcategory data for each Category collected above.
    for category in categories:
        category.subcategories = SubCategory.objects.filter(
            category=category
        ).order_by('id')
        # This totals the amounts of the Transactions of each subcategory
        # so it can be attached to account cards.
        for subcategory in category.subcategories:
            if subcategory.type == 'expense' or subcategory.type == 'savings':
                transactions = Transaction.objects.filter(
                    subcategory=subcategory)
                subcategory.current = sum(
                    i.amount for i in transactions if i.expense
                ) - \
                    sum(i.amount for i in transactions if not i.expense)
            else:
                transactions = Transaction.objects.filter(
                    subcategory=subcategory)
                subcategory.current = -sum(
                    i.amount for i in transactions if i.expense
                ) + \
                    sum(i.amount for i in transactions if not i.expense)

    #########################################################
    #########################################################
    # Generates the data that is shown on the spent/planned/remaining table.

    # This references the categories queryset declared above to find
    # all subcateogires associated with the logged-in user
    subcategories = SubCategory.objects.filter(
        category_id__in=[category.id for category in categories]
    ).order_by('id')

    # table_reference contains the data for each subcategory seperated
    # by subcategory type. This data will be pushed to the budget
    # template as context to build the data table.
    table_reference = {
        'expense': [],
        'savings': [],
        'income': [],
    }
    for subcategory in subcategories:
        transactions = Transaction.objects.filter(
            subcategory_id=subcategory.id
        )

        ######
        # Below Logic generates variables needed for funds to be
        # calculated across multiple months' budgets
        if subcategory.fund:

            category_name = Category.objects.get(
                id=subcategory.category_id
            ).name

            # queries user's months, filters by month/year values
            # that precede the selected month.
            # filter 1: month<current month, year==current year
            # filter 2: year<current year
            previous_months = Month.objects.filter(
                user=request.user,
                month__lt=request.session['date']['month'],
                year=request.session['date']['year']
            ) | Month.objects.filter(
                user=request.user,
                year__lt=request.session['date']['year']
            )

            # These 2 values are incremented by below for loop.
            previous_amount = 0
            previous_transactions = 0

            for month in previous_months:

                if Category.objects.filter(
                    name=category_name,
                    month=month
                ).exists():

                    previous_category_id = Category.objects.get(
                        name=category_name,
                        month=month
                    ).id

                    if SubCategory.objects.filter(
                        name=subcategory.name,
                        type=subcategory.type,
                        category_id=previous_category_id,
                        fund=True
                    ).exists():

                        # previous subcategories are selected by name and
                        # category id matching the selected month.
                        previous_subcategory = SubCategory.objects.get(
                            name=subcategory.name,
                            type=subcategory.type,
                            category_id=previous_category_id
                        )

                        previous_amount += previous_subcategory.amount

                        # 'income' remaining values are reverse of expenses
                        # and savings - shows how much is left to receive,
                        # not to spend. This requires transactions flagged
                        # 'expense=False' to be subtracted and 'expense=True'
                        # to be added. expense and savings transaction are
                        # opposite.
                        if subcategory.type == 'income':
                            previous_transactions += sum(
                                transaction.amount if not transaction.expense
                                else -transaction.amount
                                for transaction in Transaction.objects.filter(
                                    subcategory_id=previous_subcategory.id
                                )
                            )
                        else:
                            previous_transactions += sum(
                                transaction.amount if transaction.expense
                                else -transaction.amount
                                for transaction
                                in Transaction.objects.filter(
                                    subcategory_id=previous_subcategory.id
                                )
                            )
        ######

        if subcategory.type == 'expense':
            # spent - expenses are added and income is subtracted so in
            # the table display the the spent column will show a positive
            # figure indicating a positive amount has been spent.
            spent = 0+(sum(
                i.amount for i in transactions if i.expense is True
            )) - \
                (sum(i.amount for i in transactions if i.expense is False))
            previous_remaining = 0
            if subcategory.fund:
                # previous_amount and previous_transactions are calc'ed in
                # fund logic above
                previous_remaining = previous_amount-previous_transactions
            expense_data = {
                'category': Category.objects.get(subcategory=subcategory).name,
                'subcategory': subcategory.name,
                'spent': spent,
                'planned': subcategory.amount,
                'remaining': subcategory.amount-spent+previous_remaining,
                'fund': subcategory.fund,
                'transactions': Transaction.objects.filter(
                    subcategory_id=subcategory.id
                ).order_by('-date')
            }
            # Transaction data will be displayed in a collapsible
            # table or card under each subcategory.
            for transaction in expense_data['transactions']:
                # This is needed if account_id has a null value.
                if transaction.account_id:
                    transaction.account = Account.objects.get(
                        id=transaction.account_id)
            table_reference['expense'].append(expense_data)
        if subcategory.type == 'income':
            # received - expenses are subtracted and income is
            # added so in the table display the the received
            # column will show a positive figure indicating a
            # positive amount has been received.  (Note - This
            # is opposite of the spent formula above.)
            received = 0-(sum(
                i.amount for i in transactions if i.expense is True)
            ) + \
                (sum(i.amount for i in transactions if i.expense is False))
            previous_remaining = 0
            if subcategory.fund:
                # previous_amount and previous_transactions are
                # calc'ed in fund logic above
                previous_remaining = previous_amount-previous_transactions
            income_data = {
                'category': Category.objects.get(subcategory=subcategory).name,
                'subcategory': subcategory.name,
                'received': received,
                'planned': subcategory.amount,
                'remaining': subcategory.amount-received+previous_remaining,
                'fund': subcategory.fund,
                'transactions': Transaction.objects.filter(
                    subcategory_id=subcategory.id
                ).order_by('-date')
            }
            # Transaction data will be displayed in a collapsible
            # table or card under each subcategory.
            for transaction in income_data['transactions']:
                # This is needed if account_id has a null value.
                if transaction.account_id:
                    transaction.account = Account.objects.get(
                        id=transaction.account_id)
            table_reference['income'].append(income_data)
        if subcategory.type == 'savings':
            # saved - expenses are added and income is subtracted
            # so in the table display the the spent column will
            # show a positive figure indicating a positive amount
            # has been spent. (This is the same as the expense formula
            # above.)
            saved = 0+(sum(
                i.amount for i in transactions if i.expense is True
            )) - \
                (sum(i.amount for i in transactions if i.expense is False))
            previous_remaining = 0
            if subcategory.fund:
                # previous_amount and previous_transactions are
                # calc'ed in fund logic above
                previous_remaining = previous_amount-previous_transactions
            savings_data = {
                'category': Category.objects.get(subcategory=subcategory).name,
                'subcategory': subcategory.name,
                'saved': saved,
                'planned': subcategory.amount,
                'remaining': subcategory.amount-saved+previous_remaining,
                'fund': subcategory.fund,
                'transactions': Transaction.objects.filter(
                    subcategory_id=subcategory.id
                ).order_by('-date'),
                # account_value is a unique column to 'savings' and
                # replaces the Fund Column as all savings subcategories
                # are required to be funds.  It is the sum of all
                # transactions in the account from current and previous
                # months.
                'account_value': previous_transactions+saved
            }
            # Transaction data will be displayed in a collapsible table or
            # card under each subcategory.
            for transaction in savings_data['transactions']:
                # This is needed if account_id has a null value.
                if transaction.account_id:
                    transaction.account = Account.objects.get(
                        id=transaction.account_id)
            table_reference['savings'].append(savings_data)
    # This sorts the table data so it is displayed with categories
    # shown together in the budget table.
    table_reference['expense'] = sorted(
        table_reference['expense'], key=lambda d: d['category'])
    table_reference['savings'] = sorted(
        table_reference['savings'], key=lambda d: d['category'])
    table_reference['income'] = sorted(
        table_reference['income'], key=lambda d: d['category'])
    totals_reference = {
        'expenses_spent_total': sum(i['spent']
                                    for i in table_reference['expense']),
        'expenses_planned_total': sum(i['planned']
                                      for i in table_reference['expense']),
        'expenses_remaining_total': sum(i['remaining']
                                        for i in table_reference['expense']),
        'income_received_total': sum(i['received']
                                     for i in table_reference['income']),
        'income_planned_total': sum(i['planned']
                                    for i in table_reference['income']),
        'income_remaining_total': sum(i['remaining']
                                      for i in table_reference['income']),
        'savings_saved_total': sum(i['saved']
                                   for i in table_reference['savings']),
        'savings_planned_total': sum(i['planned']
                                     for i in table_reference['savings']),
        'savings_remaining_total': sum(i['remaining']
                                       for i in table_reference['savings']),
    }

    over_under = totals_reference['income_planned_total'] - \
        totals_reference['expenses_planned_total'] - \
        totals_reference['savings_planned_total']
    if over_under > 0:
        totals_reference['over_under'] = f"{over_under} Under Budget!"
    elif over_under < 0:
        totals_reference['over_under'] = f"{abs(over_under)} Over Budget!"
    else:
        totals_reference['over_under'] = 'Right on Budget!'

    data = {
        'categories': categories,
        'table_reference': table_reference,
        'totals_reference': totals_reference,
    }
    return data
        

@login_required
def budget_dashboard(request):
    """
    Generates User Budget Dashboard.
    """

    if request.method == 'POST':
        form = forms.MonthSelectForm(request.POST)
        if form.is_valid():
            # Updates month_year session data values.
            date_data = form.cleaned_data['month_year'].split('-')
            request.session['date'] = {
                'month': int(date_data[0]),
                'year': int(date_data[1])
            }
    else:
        form = forms.MonthSelectForm()

        # This sets month/year data equal to the current month/year in
        # the event that there is not sessions data for these values
        # or if an associated Object for the current month does not
        # exist.  This will occur when the user clicks 'Cancel' on
        # the Create New Month screen.
        if 'date' not in request.session or \
                not Month.objects.filter(
                    user=request.user,
                    month=request.session['date']['month'],
                    year=request.session['date']['year']
                ).exists():
            current_month = datetime.now().month
            current_year = datetime.now().year

            request.session['date'] = {
                'month': current_month,
                'year': current_year
            }

    # This logic checks to see if the logged in user has created any
    # Months to attach a budget to. If they have not, it redirects
    # them to the page to create their first month.
    budgets_exist = Month.objects.filter(user=request.user)
    if not budgets_exist:
        return HttpResponseRedirect(reverse('budget:first_month'))

    month_exists = Month.objects.filter(
        user=request.user,
        month=request.session['date']['month'],
        year=request.session['date']['year']
    )
    if not month_exists:
        return HttpResponseRedirect(reverse('budget:new_month'))

    # If there was no session data on page load, default login
    # values for Month and Year will be the current month and year.
    form_month = request.session['date']['month']
    form_year = request.session['date']['year']
    form.fields['month_year'].initial = f"{form_month}-{form_year}"

    # limits month_year choices to current year and next year.
    form.fields['month_year'].choices = [
        (f"{month}-{year}", f"{month_reference_dict[month]}, {year}")
        for year in range(datetime.now().year-2, datetime.now().year + 3)
        for month in range(1, 13)
    ]

    month = month_reference_dict_full[request.session['date']['month']]
    year = request.session['date']['year']
    month_id = Month.objects.get(
        user = request.user,
        month = request.session['date']['month'],
        year = request.session['date']['year']
    ).id
    data = collect_dashboard_table_data(request)
    context = {
        'form': form,
        'categories': data['categories'],
        'table_reference': data['table_reference'],
        'totals_reference': data['totals_reference'],
        'month': month,
        'year': year,
        'month_id': month_id,
        'source': 'dashboard',
        'title': 'Budget Dashboard',
    }

    return render(request, 'budget/budget.html', context=context)


def budget_table(request):
    month = month_reference_dict_full[request.session['date']['month']]
    year = request.session['date']['year']
    data = collect_dashboard_table_data(request)
    context = {
        'categories': data['categories'],
        'table_reference': data['table_reference'],
        'totals_reference': data['totals_reference'],
        'month': month,
        'year': year,
    }
    return render(request, 'budget/budget_table.html', context=context)


class FirstMonthCreateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    CreateView
):
    """Creates First User Month on Initial Login."""
    form_class = forms.MonthForm
    model = Month
    template_name = 'budget/first_month_form.html'
    success_url = reverse_lazy('budget:budget_dashboard')

    # Copy is a field that is used in the NewMonthCreateForm. Default
    # Value is set to False so it can be disregarded in the
    # FirstMonthCreate functionality.
    def get_initial(self):
        initial = {
            'user': self.request.user,
            'month': self.request.session['date']['month'],
            'year': self.request.session['date']['year'],
            'month_year': None,
            'copy': False,
        }
        return initial

    def test_func(self):
        if not Month.objects.filter(user=self.request.user):
            return True
        return False

    def form_valid(self, form):
        # form.cleaned_data example - {'user': <User: test3@test.com>,
        # 'month': 2, 'year': 2023, 'copy': False}
        first_month = Month.objects.create(
            month=form.cleaned_data['month'],
            year=form.cleaned_data['year'],
            user=self.request.user
        )
        Category.objects.create(
            name='Income',
            month=first_month
        )
        Category.objects.create(
            name='Savings',
            month=first_month
        )
        return HttpResponseRedirect(reverse('budget:budget_dashboard'))

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title'] = 'First Month'
        return context


class NewMonthCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Creates new user months."""
    form_class = forms.MonthForm
    model = Month
    template_name = 'budget/new_month_form.html'

    def get_initial(self):
        current_month = datetime.now().month
        current_year = datetime.now().year

        current_month_exists = Month.objects.filter(
            user = self.request.user,
            month = current_month,
            year = current_year,
        ).exists()
        
        if current_month_exists:
            initial_month_year = f"{current_month}-{current_year}"
        else:
            recent_mth = Month.objects.filter(
                user = self.request.user,
                month__lte = current_month,
                year__lte = current_year,
            ).order_by('-year', '-month')[0]
            initial_month_year = f"{recent_mth.month}-{recent_mth.year}"
        
        initial = {
            'user': self.request.user,
            'month': self.request.session['date']['month'],
            'year': self.request.session['date']['year'],
            'month_year': initial_month_year,
            'copy': True
        }
        return initial
    
    def get_form(self, form_class = None):
        form = super().get_form(form_class)
        user_months = Month.objects.filter(
            user = self.request.user,
        ).order_by('year', 'month')
        month_choices = [
            (
                f"{month.month}-{month.year}",
                f"{month_reference_dict_full[month.month]}, {month.year}"
            )
            for month in user_months
        ]
        form.fields['month_year'].choices = month_choices
        return form

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title'] = 'New Month'
        return context

    def test_func(self):
        month_exists = Month.objects.filter(
            user=self.request.user,
            month=self.request.session['date']['month'],
            year=self.request.session['date']['year']
        )
        if month_exists:
            return False
        return True

    def form_valid(self, form):
        # form.cleaned_data example:
        # { 'user': <User: test@example.com>, 
        #   'month_year': '4-2023', 
        #   'copy': True }
        parsed_month_year = form.cleaned_data['month_year'].split('-')
        form_month = int(parsed_month_year[0])
        form_year = int(parsed_month_year[1])
        
        if form.cleaned_data['copy']:
            month_to_copy = Month.objects.get(
                user = self.request.user,
                month = form_month,
                year = form_year,
            )
            # creates new month using data pass in from form.
            new_month = Month.objects.create(
                month=form.cleaned_data['month'],
                year=form.cleaned_data['year'],
                user=form.cleaned_data['user']
            )
            # finds all categories associated with the selected month.
            month_to_copy_categories = Category.objects.filter(
                month=month_to_copy
            ).order_by('id')
            for category in month_to_copy_categories:
                # recreates the selected month's categories using
                # the id of the new month.
                new_category = Category.objects.create(
                    name=category.name,
                    month_id=new_month.id
                )
                # finds all subcategories associated with the current
                # category from the selected month.
                subcategories = SubCategory.objects.filter(
                    category=category
                ).order_by('id')
                # recreates the selected category's subcategories
                # using the new category's id.
                for subcategory in subcategories:
                    SubCategory.objects.create(
                        name=subcategory.name,
                        category_id=new_category.id,
                        fund=subcategory.fund,
                        amount=subcategory.amount,
                        type=subcategory.type
                    )
        # below else statement creates a blank month is Copy == False.
        else:
            new_month = Month.objects.create(
                month=form.cleaned_data['month'],
                year=form.cleaned_data['year'],
                user=form.cleaned_data['user']
            )
        return HttpResponseRedirect(reverse('budget:budget_dashboard'))
    

class MonthDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DeleteView
):
    """Deletes User Months."""
    model = Month
    template_name = 'budget/month_delete.html'
    success_url = reverse_lazy('budget:budget_dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Month'
        context['month_id'] = self.kwargs['pk']
        context['month'] = Month.objects.get(
            id=context['month_id'])
        context['month_name'] = month_reference_dict_full[
            context['month'].month
        ]
        context['year'] = context['month'].year
        return context

    def test_func(self, *args, **kwargs):
        # Verifies month is associated with logged in user
        # if the url is manually updated.
        user_month_ids = [
            i.id for i in Month.objects.filter(user=self.request.user)]
        if self.kwargs['pk'] not in user_month_ids:
            return False
        return True


class AccountCreateView(LoginRequiredMixin, CreateView):
    """Creates new user Accounts."""
    form_class = forms.AccountForm
    model = Account
    template_name = 'budget/account.html'

    def get_initial(self):
        initial = {
            'user': self.request.user
        }
        return initial

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title'] = 'Create Account'
        # template displays list view of existing accounts.
        context['accounts'] = Account.objects.filter(
            user=self.request.user
        ).order_by('id')
        # source is used to route back button in Navbar.
        context['origin'] = 'create'
        context['source'] = self.kwargs['source']
        context['vals'] = self.request.GET.get('vals', '')
        # If Create Account View is entered from Update Transaction
        # View, Transaction Data is attached to the url as a string.
        # The Back Button and Success URL will use that url data
        # to get back to the correct transaction after an account is created.
        transaction_data = context['vals'].split('/')
        if len(transaction_data) == 3:
            context['trans_source'] = transaction_data[0]
            context['trans_sub_id'] = transaction_data[1]
            context['trans_pk'] = transaction_data[2]
        return context

    def get_success_url(self, **kwargs):
        vals = self.request.GET.get('vals', '')
        transaction_data = vals.split('/')
        if len(transaction_data) == 3:
            trans_source = transaction_data[0]
            trans_sub_id = transaction_data[1]
            trans_pk = transaction_data[2]
        # If the Create Account link is clicked in the Dashboard.
        if self.kwargs['source'] == 'dashboard':
            return reverse_lazy('budget:budget_dashboard')
        # If the Create Account link is clicked from within a Create
        # Transaction View.
        if self.kwargs['source'] == 'create':
            # If a user enters the Transaction Create View from within a
            # subcategory, data will be attached to the url as a urlconf.
            # my_reverse func preserves that urlconf and passes it back
            # to the url when reverse is called so the default values
            # are the same when it returns to the transaction view.
            return my_reverse('budget:transaction', additional=vals)
        # If the Create Account Link is clicked from within an Update
        # Transaction View.
        if self.kwargs['source'] in {'subcategory_view', 'list_view'}:
            return reverse('budget:update_transaction', kwargs={
                'source': trans_source,
                'subcategory_id': trans_sub_id,
                'pk': trans_pk,
            })


class AccountUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Updates existing User Accounts."""
    form_class = forms.AccountForm
    model = Account
    template_name = 'budget/account.html'
    success_url = reverse_lazy('budget:budget_dashboard')

    def get_success_url(self, **kwargs):
        if self.kwargs['origin'] == 'create':
            return reverse('budget:account', kwargs={
                'source': 'dashboard',
            })
        if self.kwargs['origin'] == 'list':
            return reverse('budget:account_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Account'
        context['pk'] = self.kwargs['pk']
        # origin is used to route back button in Navbar.
        context['origin'] = self.kwargs['origin']
        # source is used to route successurls in account views
        # accessed from transaction views.
        context['source'] = 'account_update'
        return context

    def test_func(self, **kwargs):
        # Verifies account is associated with logged in user if
        # the url is manually updated.
        user_account_ids = [
            i.id for i in Account.objects.filter(user=self.request.user)]
        if self.kwargs['pk'] not in user_account_ids:
            return False
        return True


class AccountListView(LoginRequiredMixin, ListView):
    """Lists all existing user accounts."""
    model = Account
    template_name = 'budget/account_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Accounts'
        user_accounts = Account.objects.filter(
            user=self.request.user
        ).order_by('id')
        context['accounts'] = user_accounts
        # source is used to route back button in Navbar.
        context['origin'] = 'list'
        return context


class AccountDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Deletes User Accounts."""
    model = Account
    template_name = 'budget/account_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Account'
        context['pk'] = self.kwargs['pk']
        context['account'] = Account.objects.get(id=context['pk'])
        context['origin'] = self.kwargs['origin']
        return context

    def get_success_url(self, **kwargs):
        if self.kwargs['origin'] == 'create':
            return reverse('budget:budget_dashboard')
        if self.kwargs['origin'] == 'list':
            return reverse('budget:account_list')

    def test_func(self, *args, **kwargs):
        # Verifies account is associated with logged in user
        # if the url is manually updated.
        user_account_ids = [
            i.id for i in Account.objects.filter(user=self.request.user)]
        if self.kwargs['pk'] not in user_account_ids:
            return False
        return True


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Creates New User Categories."""
    form_class = forms.CategoryForm
    model = Category
    template_name = 'budget/category.html'
    success_url = reverse_lazy('budget:budget_dashboard')

    def get_initial(self):
        # hidden field associates created account with selected month.
        initial = {
            'month': Month.objects.get(
                user=self.request.user,
                month=self.request.session['date']['month'],
                year=self.request.session['date']['year']
            )
        }
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Category'
        return context


class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Updates existing User Categories."""
    form_class = forms.CategoryForm
    model = Category
    template_name = 'budget/category.html'
    success_url = reverse_lazy('budget:budget_dashboard')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title'] = 'Update Category'
        context['category_id'] = self.kwargs['pk']
        return context

    def test_func(self, **kwargs):
        # If a user manually enters a value in the url for <int:pk>, this
        # makes sure the id of the Category they are updating is associated
        # with their User Account.
        user_month_ids = [
            i.id for i in Month.objects.filter(user=self.request.user)]
        user_category_ids = [i.id for i in Category.objects.filter(
            month_id__in=user_month_ids)]
        if self.kwargs['pk'] not in user_category_ids:
            return False
        return True


class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    "Deletes User Categories."
    model = Category
    template_name = 'budget/category_delete.html'
    success_url = reverse_lazy('budget:budget_dashboard')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title'] = 'Delete Category'
        context['pk'] = self.kwargs['pk']
        context['category'] = Category.objects.get(id=context['pk'])
        return context

    def test_func(self, *args, **kwargs):
        # If a user manually enters a value in the url for <int:pk>, this
        # makes sure the id of the Category they are updating is associated
        # with their User Account.
        user_month_ids = [
            i.id for i in Month.objects.filter(user=self.request.user)]
        user_category_ids = [i.id for i in Category.objects.filter(
            month_id__in=user_month_ids)]
        if self.kwargs['pk'] not in user_category_ids:
            return False
        return True


class SubCategoryCreateView(LoginRequiredMixin, CreateView):
    """Creates new user Subcategories"""
    form_class = forms.SubCategoryForm
    model = SubCategory
    template_name = 'budget/subcategory.html'
    success_url = reverse_lazy('budget:budget_dashboard')

    def get_initial(self, **kwargs):
        category = self.kwargs['category']
        initial = {
            'category': category
        }
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Subcategory'
        return context


class SubCategoryUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    UpdateView
):
    """Updates existing User Subcategories"""
    form_class = forms.SubCategoryForm
    model = SubCategory
    template_name = 'budget/subcategory.html'
    success_url = reverse_lazy('budget:budget_dashboard')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title'] = 'Update Subcategory'
        context['transactions'] = Transaction.objects.filter(
            subcategory=SubCategory.objects.get(
                id=self.kwargs['pk']
            )
        ).order_by('-date')
        context['subcategory_id'] = self.kwargs['pk']
        context['category_id'] = self.kwargs['category']
        context['type'] = SubCategory.objects.get(
            id=self.kwargs['pk']
        ).type
        # source is used to route back button in Navbar.
        context['source'] = 'subcategory_view'
        return context

    def test_func(self):
        # If a user manually enters a value in the url for <int:pk>, this
        # makes sure the id of the Subcategory they are updating is
        # associated with their User Account.
        user_month_ids = [
            i.id for i in Month.objects.filter(user=self.request.user)]
        user_category_ids = [i.id for i in Category.objects.filter(
            month_id__in=user_month_ids)]
        user_subcategory_ids = [i.id for i in SubCategory.objects.filter(
            category_id__in=user_category_ids)]
        if self.kwargs['pk'] not in user_subcategory_ids:
            return False
        return True


class SubCategoryDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DeleteView
):
    """Deletes User Subcategories."""
    model = SubCategory
    template_name = 'budget/subcategory_delete.html'
    success_url = reverse_lazy('budget:budget_dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Subcategory'
        context['category_id'] = self.kwargs['category']
        context['subcategory_id'] = self.kwargs['pk']
        context['subcategory'] = SubCategory.objects.get(
            id=context['subcategory_id'])
        return context

    def test_func(self, *args, **kwargs):
        # If a user manually enters a value in the url for <int:pk>,
        # this makes sure the id of the Subcategory they are updating
        # is associated with their User Account.
        user_month_ids = [
            i.id for i in Month.objects.filter(user=self.request.user)]
        user_category_ids = [i.id for i in Category.objects.filter(
            month_id__in=user_month_ids)]
        user_subcategory_ids = [i.id for i in SubCategory.objects.filter(
            category_id__in=user_category_ids)]
        if self.kwargs['pk'] not in user_subcategory_ids:
            return False
        return True


class TransactionCreateView(LoginRequiredMixin, CreateView):
    """Creates new user Transactions."""
    form_class = forms.TransactionForm
    model = Transaction
    template_name = 'budget/transaction.html'
    success_url = reverse_lazy('budget:budget_dashboard')

    def get_initial(self, *args, **kwargs):
        # vals defines the subcategory id and the type (income,
        # expense, savings) of the selected subcategory if a
        # transaction is created directly from the subcategory page.
        vals = (self.request.GET.get('vals', '')).split('/')
        if len(vals) == 2:
            type = vals[0]
            subcategory = vals[1]
        else:
            type = ''
            subcategory = ''
        initial = {
            'user': self.request.user,
            'month': self.request.session['date']['month'],
            'year': self.request.session['date']['year'],
        }
        initial['date'] = datetime.now()
        if subcategory:
            initial['subcategory'] = subcategory
        if type == 'expense' or type == 'savings':
            initial['expense'] = True
        if type == 'income':
            initial['expense'] = False

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Transaction'
        # source is used to route back button in navbar if account create is
        # entered from Transaction Create View
        context['source'] = 'create'
        context['vals'] = self.request.GET.get('vals', '')
        if context['vals']:
            vals = context['vals'].split('/')
            context['subcategory_id'] = vals[1]
            context['category_id'] = SubCategory.objects.get(
                id=context['subcategory_id']
            ).category_id
        month = Month.objects.get(
            user=self.request.user,
            month=self.request.session['date']['month'],
            year=self.request.session['date']['year']
        )
        categories = Category.objects.filter(
            month=month
        )
        subcategories = SubCategory.objects.filter(
            category__in=categories
        )
        context['subcategories_exist'] = subcategories
        return context


class TransactionUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    UpdateView
):
    """Updates existing User Transactions."""
    form_class = forms.TransactionForm
    model = Transaction
    template_name = 'budget/transaction.html'
    success_url = reverse_lazy('budget:budget_dashboard')

    def get_initial(self, *args, **kwargs):
        id = self.kwargs['pk']
        transaction = Transaction.objects.get(id=id)
        subcategory = SubCategory.objects.get(
            id=transaction.subcategory.id
        )
        category = Category.objects.get(
            id=subcategory.category.id
        )
        month = Month.objects.get(
            id=category.month.id
        )
        print(month)
        initial = {
            'user': self.request.user,
            'month': month.month,
            'year': month.year,
            'subcategory': self.kwargs['subcategory_id']
        }
        print(initial)
        return initial

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title'] = 'Update Transaction'
        context['update'] = True
        context['transaction_pk'] = self.kwargs['pk']
        context['subcategory_id'] = self.kwargs['subcategory_id']
        category_id = SubCategory.objects.get(
            id=context['subcategory_id']).category_id
        context['category_id'] = category_id
        # source is used to route back button in Navbar.

        context['source'] = self.kwargs['source']
        source = context['source']
        sub_id = context['subcategory_id']
        trans_pk = context['transaction_pk']
        context['vals'] = f"{source}/{sub_id}/{trans_pk}"
        # 'subcategories_exist' is used in Transaction Create view to display
        # a tooltip if the user has no subcategories. This can be disregarded
        # in the Transaction Update View.
        context['subcategories_exist'] = True
        return context

    def get_success_url(self, **kwargs):
        if self.kwargs['source'] == 'subcategory_view':
            return reverse_lazy('budget:budget_dashboard')
        if self.kwargs['source'] == 'list_view':
            return reverse_lazy('budget:transaction_list')

    def test_func(self, *args, **kwargs):
        # If a user manually enters a value in the url for <int:pk>, this
        # makes sure the id of the Transaction they are updating is
        # associated with their User Account.
        user_month_ids = [
            i.id for i in Month.objects.filter(user=self.request.user)]
        user_category_ids = [i.id for i in Category.objects.filter(
            month_id__in=user_month_ids)]
        user_subcategory_ids = [i.id for i in SubCategory.objects.filter(
            category_id__in=user_category_ids)]
        user_transaction_ids = [i.id for i in Transaction.objects.filter(
            subcategory_id__in=user_subcategory_ids)]
        if self.kwargs['pk'] not in user_transaction_ids:
            return False
        return True


class TransactionListView(LoginRequiredMixin, ListView):
    """List view of all of User's Transactions"""
    model = Transaction
    template_name = 'budget/transaction_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Transactions'

        # If user_transactions is empty, the user has no transactions and the
        #     table will not be displayed.
        user_month_ids = [
            i.id for i in Month.objects.filter(user=self.request.user)]
        user_category_ids = [i.id for i in Category.objects.filter(
            month_id__in=user_month_ids)]
        user_subcategory_ids = [i.id for i in SubCategory.objects.filter(
            category_id__in=user_category_ids)]
        user_transaction_ids = [i.id for i in Transaction.objects.filter(
            subcategory_id__in=user_subcategory_ids)]
        context['transactions_exist'] = user_transaction_ids

        # Generates data displayed on Table.
        user_months = [i.id for i in Month.objects.filter(
            user=self.request.user
        ).order_by('-year', '-month')]
        transaction_data = []
        for month in user_months:
            categories = Category.objects.filter(
                month_id=month
            ).order_by('id')
            subcategories = SubCategory.objects.filter(
                category__in=categories
            ).order_by('id')
            transactions = Transaction.objects.filter(
                subcategory__in=subcategories
            ).order_by('-date', 'id')
            for transaction in transactions:
                transaction.subcategory = SubCategory.objects.get(
                    id=transaction.subcategory.id
                )
                transaction.category = Category.objects.get(
                    id=transaction.subcategory.category_id
                )
                if transaction.account:
                    transaction.account = Account.objects.get(
                        id=transaction.account_id
                    )
                if transaction.expense:
                    transaction.amount = 0-transaction.amount
            month_ref = Month.objects.get(
                id=month
            )
            transaction_data.append({
                'name': month_reference_dict_full[month_ref.month],
                'year': month_ref.year,
                'transactions': transactions,
            })
        context['transaction_data'] = transaction_data

        # source is used to route back button in Navbar.
        context['source'] = 'list_view'
        return context


class TransactionDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DeleteView
):
    """Deletes User Transactions."""
    model = Transaction
    template_name = 'budget/transaction_delete.html'

    def get_success_url(self, **kwargs):
        if self.kwargs['source'] == 'subcategory_view':
            return reverse_lazy('budget:budget_dashboard')
        if self.kwargs['source'] == 'list_view':
            return reverse_lazy('budget:transaction_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Transaction'
        # source is used to route back button in Navbar.
        context['source'] = self.kwargs['source']
        context['subcategory_id'] = self.kwargs['subcategory_id']
        context['pk'] = self.kwargs['pk']
        transaction = Transaction.objects.get(id=context['pk'])
        context['transaction'] = f"${transaction.amount}"
        return context

    def test_func(self, *args, **kwargs):
        # If a user manually enters a value in the url for <int:pk>, this
        # makes sure the id of the Transaction they are updating is
        # associated with their User Account.
        user_month_ids = [
            i.id for i in Month.objects.filter(user=self.request.user)]
        user_category_ids = [i.id for i in Category.objects.filter(
            month_id__in=user_month_ids)]
        user_subcategory_ids = [i.id for i in SubCategory.objects.filter(
            category_id__in=user_category_ids)]
        user_transaction_ids = [i.id for i in Transaction.objects.filter(
            subcategory_id__in=user_subcategory_ids)]
        if self.kwargs['pk'] not in user_transaction_ids:
            return False
        return True
