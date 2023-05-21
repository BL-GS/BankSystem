from django.contrib import admin
from BankManagement.models import *

# Register your models here.
admin.site.register(CheckAccount)
admin.site.register(Employee)
admin.site.register(Customer)
admin.site.register(CustomerToCA)