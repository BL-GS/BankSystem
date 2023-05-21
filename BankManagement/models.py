from django.db import models


MAX_CHAR_LEN = 255


class CheckAccount(models.Model):
    CAccount_ID = models.CharField('CAccount_ID', primary_key=True, max_length=MAX_CHAR_LEN)
    CAccount_Balance = models.DecimalField('CAccount_Balance', max_digits=20, decimal_places=2, blank=False)
    CAccount_Open_Date = models.DateTimeField('CAccount_Open_Date', blank=False)
    class Meta:
        db_table = 'CheckAccount'


class Employee(models.Model):
    Employee_ID = models.CharField('Employee_ID', max_length=18, primary_key=True)
    Employee_Name = models.CharField('Employee_Name', max_length=MAX_CHAR_LEN, blank=False)
    Employee_Hire_Date = models.DateTimeField('Employee_Hire_Date', blank=False)

    class Meta:
        db_table = 'Employee'


class Customer(models.Model):
    Customer_ID = models.CharField('Customer_ID', primary_key=True, max_length=18)
    Customer_Name = models.CharField('Customer_Name', max_length=MAX_CHAR_LEN, blank=False)
    Customer_Phone_Number = models.DecimalField('Customer_Phone_Number', max_digits=11, decimal_places=0, blank=False)

    class Meta:
        db_table = 'Customer'

class CustomerToCA(models.Model):
    CAccount_Last_Access_Date = models.DateTimeField('CAccount_Last_Access_Date', auto_now=True)

    CAccount_ID = models.ForeignKey(CheckAccount, on_delete=models.CASCADE)
    Customer_ID = models.ForeignKey(Customer, on_delete=models.PROTECT)

    class Meta:
        db_table = 'CustomerToCA'
        constraints = [
            # models.UniqueConstraint(fields=['Customer_ID', 'CAccount_Open_Bank_Name'], name='One customer is only allowed to open one CA in one bank'),
            # models.UniqueConstraint(fields=['CAccount_ID', 'Customer_ID'], name='CustomerToCA Fake Primary Key')
        ]


class SavingAccount(models.Model):
    SAccount_ID = models.CharField('SAccount_ID', primary_key=True, max_length=MAX_CHAR_LEN)
    SAccount_Balance = models.DecimalField('SAccount_Balance', max_digits=20, decimal_places=2, blank=False)
    SAccount_Open_Date = models.DateTimeField('SAccount_Open_Date', blank=False)

    class Meta:
        db_table = 'SavingAccount'


class CustomerToSA(models.Model):
    SAccount_Last_Access_Date = models.DateTimeField('SAccount_Last_Access_Date', auto_now=True)

    SAccount_ID = models.ForeignKey(SavingAccount, on_delete=models.CASCADE)
    Customer_ID = models.ForeignKey(Customer, on_delete=models.PROTECT)

    class Meta:
        db_table = 'CustomerToSA'
        constraints = [
            # models.UniqueConstraint(fields=['Customer_ID', 'SAccount_Open_Bank_Name'], name='One customer is only allowed to open one SA in one bank'),
            # models.UniqueConstraint(fields=['SAccount_ID', 'Customer_ID'], name='CustomerToSA Fake Primary Key')
        ]
