from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.http import HttpResponse
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from rest_framework import viewsets, status
from rest_framework.response import Response
from BankManagement.serializers import *
from rest_framework.permissions import AllowAny
import datetime


# Create your views here.

def init(request):
    return HttpResponse("Finish init.")


class CheckAccountViewSet(viewsets.ModelViewSet):
    '''
    Viewset for check account
    '''
    permission_classes = (AllowAny,)

    def list(self, request):
        role = request.session.get('role')
        if role == 'customer':
            id = request.session.get('user_id')
            cond_queryset = CustomerToCA.objects.filter(Customer_ID=id)
            queryset = CheckAccount.objects.filter(CAccount_ID__in=cond_queryset.values('CAccount_ID'))
        else:
            queryset = CheckAccount.objects.all()

        serializer = CheckAccountSerializer(queryset, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request):
        checkaccount = request.data.copy()

        try:
            checkaccount.pop('Customer_ID')
        except KeyError as e:
            return Response({
                'status': 'Failed',
                'message': 'Customer_ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        ca_to_customer = request.data.copy()

        try:
            ca_to_customer.pop('CAccount_Balance')
        except KeyError as e:
            return Response({
                'status': 'Failed',
                'message': 'More information is required'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = Customer.objects.filter(pk=request.data.get('Customer_ID'))
        if not queryset.exists():
            return Response({
                'status': 'Failed',
                'message': 'Customer not exist'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                checkaccount['CAccount_Open_Date'] = datetime.datetime.now()
                ca_serializer = CheckAccountSerializer(data=checkaccount)

                if ca_serializer.is_valid():
                    CheckAccount.objects.create(**ca_serializer.validated_data)

                    ca_to_customer['CAccount_Last_Access_Date'] = datetime.datetime.now()

                    ca_to_customer_serializer = CustomerToCASerializer(data=ca_to_customer)
                    if ca_to_customer_serializer.is_valid():
                        CustomerToCA.objects.create(**ca_to_customer_serializer.validated_data)

        except IntegrityError as e:
            return Response({
                'status': 'Bad request',
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'Success',
            'message': 'Create new Check Account Successfully'}, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        queryset = CheckAccount.objects.all()
        checkaccount = get_object_or_404(queryset, pk=pk)
        serializer = CheckAccountSerializer(checkaccount)
        return Response(serializer.data)

    @transaction.atomic
    def update(self, request, pk=None):
        # Only balance and overdraft are allowed to modify
        queryset = CheckAccount.objects.filter(pk=pk)
        if not queryset.exists():
            return Response({
                'status': 'Failed',
                'message': 'Check Account not exist'}, status=status.HTTP_400_BAD_REQUEST)
        if pk != request.data.get("CAccount_ID"):
            return Response({
                'status': 'Failed',
                'message': 'Could not change CAccount_ID'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                queryset.update(
                    CAccount_ID=pk,
                    CAccount_Balance=request.data.get('CAccount_Balance') if request.data.get('CAccount_Balance') else
                    queryset[0].CAccount_Balance,
                )
                queryset = CustomerToCA.objects.filter(CAccount_ID=pk)
                queryset.update(
                    CAccount_Last_Access_Date=datetime.datetime.now()
                )
        except IntegrityError as e:
            return Response({
                'status': 'Bad request',
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'Success',
            'message': 'Update Check Account Successfully'}, status=status.HTTP_200_OK)

    @transaction.atomic
    def destroy(self, request, pk=None):
        queryset = CheckAccount.objects.all()
        checkaccount = get_object_or_404(queryset, pk=pk)
        queryset = CustomerToCA.objects.all()
        customer_to_ca = get_list_or_404(queryset, CAccount_ID=pk)
        try:
            with transaction.atomic():
                for obj in customer_to_ca:
                    obj.delete()
                checkaccount.delete()
        except IntegrityError as e:
            return Response({
                'status': 'Bad request',
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'Success',
            'message': 'Delete Check Account Successfully'}, status=status.HTTP_200_OK)


class EmployeeViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    def create(self, request):
        serializer = EmployeeSerializer(data=request.data)

        if serializer.is_valid():
            if User.objects.filter(username=request.data.get('Employee_ID')):
                return Response({
                    'status': 'Bad request',
                    'message': 'User exists',
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                User.objects.create_user(
                    username=request.data.get('Employee_ID'),
                    password=request.data.get('Employee_ID'),
                    is_staff=True
                )

            Employee.objects.create(**serializer.validated_data)
            return Response({
                'status': 'Success',
                'message': 'Create new Employee Successfully'}, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'Bad request',
            'message': 'Invalid data',
        }, status=status.HTTP_400_BAD_REQUEST)


class CustomerViewSet(viewsets.ViewSet):
    '''
    Viewset for customer
    '''
    permission_classes = (AllowAny,)

    def list(self, request):
        role = request.session.get('role')

        if role == 'customer':
            id = request.session.get('user_id')
            queryset = Customer.objects.filter(pk=id)
        else:
            queryset = Customer.objects.all()

        serializer = CustomerSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = CustomerSerializer(data=request.data)

        if serializer.is_valid():
            id = request.data.get('Customer_ID')
            if User.objects.filter(username=id):
                user = authenticate(username=id)
                if user and not user.is_active:
                    user = User.objects.get(username=id)
                    user.is_active = True
                    user.save()
                else:
                    return Response({
                        'status': 'Bad request',
                        'message': 'User exists',
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                User.objects.create_user(username=id, password=id)

            Customer.objects.create(**serializer.validated_data)
            return Response({
                'status': 'Success',
                'message': 'Create new Customer Successfully'}, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'Bad request',
            'message': 'Invalid data',
        }, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        queryset = Customer.objects.all()
        customer = get_object_or_404(queryset, pk=pk)
        serializer = CustomerSerializer(customer)
        return Response(serializer.data)

    @transaction.atomic
    def update(self, request, pk=None):
        queryset = Customer.objects.filter(pk=pk)
        if not queryset.exists():
            return Response({
                'status': 'Failed',
                'message': 'Customer not exist'}, status=status.HTTP_400_BAD_REQUEST)
        if pk != request.data.get("Customer_ID"):
            return Response({
                'status': 'Failed',
                'message': 'Could not change Customer_ID'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            queryset.update(
                Customer_Name=request.data.get("Customer_Name") if request.data.get("Customer_Name") else queryset[
                    0].Customer_Name,
                Customer_Phone_Number=request.data.get("Customer_Phone_Number") if request.data.get(
                    "Customer_Phone_Number") else queryset[0].Customer_Phone_Number,
            )
        return Response({
            'status': 'Success',
            'message': 'Update data Successfully'}, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        queryset = Customer.objects.all()
        customer = get_object_or_404(queryset, pk=pk)
        try:
            user = User.objects.get(username=customer.Customer_ID)
            user.is_active = False
            user.save()

            customer.delete()
        except ProtectedError as e:
            return Response({
                'status': 'Failed',
                'message': 'Could not delete'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'status': 'Success',
            'message': 'Delete data Successfully'}, status=status.HTTP_200_OK)


class LoginViewSet(viewsets.ViewSet):
    '''
    Viewset for customer
    '''
    permission_classes = (AllowAny,)

    def create(self, request):
        info = request.data.copy()

        try:
            info.pop('ope')
        except KeyError as e:
            return Response({
                'status': 'Failed',
                'message': 'Unknown operation'}, status=status.HTTP_400_BAD_REQUEST)

        if request.data.get('ope') == 'Logout':
            logout(request)
            return Response({
                'status': 'Success',
                'message': 'Delete data Successfully'}, status=status.HTTP_200_OK)

        try:
            info.pop('ID')
        except KeyError as e:
            return Response({
                'status': 'Failed',
                'message': 'ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        id = request.data.get('ID')
        if User.objects.filter(username=id):
            # 使用内置方法验证
            user = authenticate(username=id, password=id)
            if user and user.is_active:
                login(request, user)
                request.session['user_id'] = id

                if Employee.objects.filter(pk=id).exists():
                    request.session['role'] = 'employee'
                elif Customer.objects.filter(pk=id).exists():
                    request.session['role'] = 'customer'
                else:
                    request.session['role'] = 'supervisor'

                return Response({
                    'status': 'Success',
                    'message': 'Login Successfully'}, status=status.HTTP_201_CREATED)
        return Response({
            'status': 'Failed',
            'message': 'Failed Login'}, status=status.HTTP_400_BAD_REQUEST)


class CustomerToCAViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    queryset = CustomerToCA.objects.all()
    serializer_class = CustomerToCASerializer


class SavingAccountViewSet(viewsets.ViewSet):
    '''
    Viewset for saving account
    '''
    permission_classes = (AllowAny,)

    def list(self, request):
        role = request.session.get('role')

        if role == 'customer':
            id = request.session.get('user_id')
            cond_queryset = CustomerToSA.objects.filter(Customer_ID=id)
            queryset = SavingAccount.objects.filter(SAccount_ID__in=cond_queryset.values('SAccount_ID'))
        else:
            queryset = SavingAccount.objects.all()

        serializer = SavingAccountSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        savingaccount = request.data.copy()

        try:
            savingaccount.pop('Customer_ID')
        except KeyError as e:
            return Response({
                'status': 'Failed',
                'message': 'Customer_ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            sa_to_customer = request.data.copy()
            sa_to_customer.pop('SAccount_Balance')
        except KeyError as e:
            return Response({
                'status': 'Failed',
                'message': 'More information is required'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = Customer.objects.filter(
            pk=request.data.get('Customer_ID'))
        if not queryset.exists():
            return Response({
                'status': 'Failed',
                'message': 'Customer not exist'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        savingaccount['SAccount_Open_Date'] = datetime.datetime.now()
        sa_serializer = SavingAccountSerializer(data=savingaccount)

        try:
            with transaction.atomic():
                if sa_serializer.is_valid():
                    SavingAccount.objects.create(**sa_serializer.validated_data)
                    sa_to_customer['SAccount_Last_Access_Date'] = datetime.datetime.now()

                    sa_to_customer_serializer = CustomerToSASerializer(
                        data=sa_to_customer)
                    if sa_to_customer_serializer.is_valid():
                        CustomerToSA.objects.create(
                            **sa_to_customer_serializer.validated_data)
        except IntegrityError as e:
            return Response({
                'status': 'Bad request',
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'Success',
            'message': 'Create new Saving Account Successfully'}, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        queryset = SavingAccount.objects.all()
        savingaccount = get_object_or_404(queryset, pk=pk)
        serializer = SavingAccountSerializer(savingaccount)
        return Response(serializer.data)

    @transaction.atomic
    def update(self, request, pk=None):
        # Only balance and overdraft are allowed to modify
        queryset = SavingAccount.objects.filter(pk=pk)
        if not queryset.exists():
            return Response({
                'status': 'Failed',
                'message': 'Check Account not exist'}, status=status.HTTP_400_BAD_REQUEST)

        if pk != request.data.get("SAccount_ID"):
            return Response({
                'status': 'Failed',
                'message': 'Could not change SAccount_ID'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                if request.data.get('ope') == 'edit':
                    queryset.update(
                        SAccount_ID=pk,
                        SAccount_Balance=request.data.get('SAccount_Balance') if request.data.get(
                            'SAccount_Balance') else
                        queryset[0].SAccount_Balance,
                    )
                    queryset = CustomerToSA.objects.filter(SAccount_ID=pk)
                    queryset.update(
                        SAccount_Last_Access_Date=datetime.datetime.now()
                    )
                elif request.data.get('ope') == 'transfer':
                    target_queryset = SavingAccount.objects.filter(pk=request.data.get('Target_SAccount_ID'))
                    if not target_queryset.exists():
                        return Response({
                            'status': 'Failed',
                            'message': 'Target Check Account not exist'}, status=status.HTTP_400_BAD_REQUEST)

                    transfer_amount = int(request.data.get('Transfer_Amount'))
                    if transfer_amount <= 0 or transfer_amount > queryset[0].SAccount_Balance:
                        return Response({
                            'status': 'Failed',
                            'message': 'Invalid transfer amount'}, status=status.HTTP_400_BAD_REQUEST)

                    queryset.update(
                        SAccount_Balance=queryset[0].SAccount_Balance - transfer_amount
                    )
                    target_queryset.update(
                        SAccount_Balance=target_queryset[0].SAccount_Balance + transfer_amount
                    )
                    queryset = CustomerToSA.objects.filter(SAccount_ID=pk)
                    queryset.update(
                        SAccount_Last_Access_Date=datetime.datetime.now()
                    )
                    target_queryset = CustomerToSA.objects.filter(SAccount_ID=request.data.get('Target_SAccount_ID'))
                    target_queryset.update(
                        SAccount_Last_Access_Date=datetime.datetime.now()
                    )

        except IntegrityError as e:
            return Response({
                'status': 'Bad request',
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'Success',
            'message': 'Update Check Account Successfully'}, status=status.HTTP_200_OK)

    @transaction.atomic
    def destroy(self, request, pk=None):
        queryset = SavingAccount.objects.all()
        savingaccount = get_object_or_404(queryset, pk=pk)
        queryset = CustomerToSA.objects.all()
        customer_to_sa = get_list_or_404(queryset, SAccount_ID=pk)
        try:
            with transaction.atomic():
                for obj in customer_to_sa:
                    obj.delete()
                savingaccount.delete()
        except IntegrityError as e:
            return Response({
                'status': 'Bad request',
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'status': 'Success',
            'message': 'Delete Saving Account Successfully'}, status=status.HTTP_200_OK)


class CustomerToSAViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    queryset = CustomerToSA.objects.all()
    serializer_class = CustomerToSASerializer
