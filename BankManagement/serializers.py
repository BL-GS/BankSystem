from rest_framework import serializers
from BankManagement.models import *


class CheckAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckAccount
        fields = ('CAccount_ID', 'CAccount_Balance', 'CAccount_Open_Date')


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ('Employee_ID', 'Employee_Name', 'Employee_Hire_Date')


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ('Customer_ID', 'Customer_Name', 'Customer_Phone_Number')

class CustomerToCASerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerToCA
        fields = ('CAccount_ID', 'Customer_ID', 'CAccount_Last_Access_Date')

class SavingAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingAccount
        fields = ('SAccount_ID', 'SAccount_Balance', 'SAccount_Open_Date')


class CustomerToSASerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerToSA
        #           'SAccount_Open_Bank_Name', 'SAccount_Last_Access_Date')
        fields = ('SAccount_ID', 'Customer_ID', 'SAccount_Last_Access_Date')
