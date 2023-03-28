"""
Models for life_caddie_django application
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(
        auto_now_add=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name


class Month(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.IntegerField(max_length=4)

    def __str__(self):
        return f"{self.month}/{self.year}"

    class Meta:
        unique_together = ('month', 'user', 'year')


class Category(models.Model):
    month = models.ForeignKey(Month, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('month', 'name')


class SubCategory(models.Model):

    fund_choices = (
        (False, 'No'),
        (True, 'Yes'),
    )

    type_choices = (
        ('expense', 'Expense'),
        ('savings', 'Savings'),
        ('income', 'Income'),
    )

    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    fund = models.BooleanField(
        null=True, blank=True, default=False, choices=fund_choices)
    amount = models.DecimalField(max_digits=11, decimal_places=2,
                                 validators=[MinValueValidator(0)])
    type = models.CharField(
        max_length=10, default='expense', choices=type_choices)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    expense_choices = (
        (True, 'Expense/Savings Deposit'),
        (False, 'Income/Savings Withdrawal'),
    )
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
    expense = models.BooleanField(default=True, choices=expense_choices)
    date = models.DateField()
    amount = models.DecimalField(max_digits=11, decimal_places=2,
                                 validators=[MinValueValidator(0)])
    vendor = models.CharField(max_length=200)
    account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
