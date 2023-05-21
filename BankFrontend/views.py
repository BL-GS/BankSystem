from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.urls import reverse


# Create your views here.

def index(request):
    return render(request, 'BankFrontend/index.html')


def login_index(request):
    return render(request, 'BankFrontend/dist/login.html')


def dist_index(request):
    return render(request, 'BankFrontend/dist/index.html')


@login_required(login_url='login.html')
def customers_index(request):
    return render(request, 'BankFrontend/dist/customers.html')


@login_required(login_url='login.html')
def checkaccounts_index(request):
    return render(request, 'BankFrontend/dist/checkaccounts.html')


@login_required(login_url='login.html')
def savingaccounts_index(request):
    return render(request, 'BankFrontend/dist/savingaccounts.html')


@login_required(login_url='login.html')
def employees_index(request):
    return render(request, 'BankFrontend/dist/employees.html')


def bad_request_index(request):
    return render(request, 'BankFrontend/dist/400.html')


def not_found_index(request):
    return render(request, 'BankFrontend/dist/404.html')


def internal_server_error_index(request):
    return render(request, 'BankFrontend/dist/500.html')
