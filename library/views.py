from datetime import timedelta

import rest_framework.serializers
from django.db.models import Count, OuterRef, Subquery, fields, IntegerField
from rest_framework import viewsets, status, serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from .models import Author, Book, Member, Loan
from .serializers import AuthorSerializer, BookSerializer, MemberSerializer, LoanSerializer, TopMemberSerializer
from rest_framework.decorators import action
from django.utils import timezone
from .tasks import send_loan_notification

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related("author")

        return qs

    @action(detail=True, methods=['post'])
    def loan(self, request, pk=None):
        book = self.get_object()
        if book.available_copies < 1:
            return Response({'error': 'No available copies.'}, status=status.HTTP_400_BAD_REQUEST)
        member_id = request.data.get('member_id')
        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            return Response({'error': 'Member does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan = Loan.objects.create(book=book, member=member)
        book.available_copies -= 1
        book.save()
        send_loan_notification.delay(loan.id)
        return Response({'status': 'Book loaned successfully.'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        book = self.get_object()
        member_id = request.data.get('member_id')
        try:
            loan = Loan.objects.get(book=book, member__id=member_id, is_returned=False)
        except Loan.DoesNotExist:
            return Response({'error': 'Active loan does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan.is_returned = True
        loan.return_date = timezone.now().date()
        loan.save()
        book.available_copies += 1
        book.save()
        return Response({'status': 'Book returned successfully.'}, status=status.HTTP_200_OK)




class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

    @action(detail=False, methods=("GET",), serializer_class=TopMemberSerializer)
    def top_active(self, request, pk=None):
        serializer = self.get_serializer_class()

        loans = Loan.objects.filter(is_returned=False, member=OuterRef("pk"))

        members = Member.objects.all().annotate(
            loan_count=Subquery(loans), output_field=IntegerField(),
        )[:5]

        data = serializer(members, many=True).data

        return Response(data)

class ExtendDueDateSerializer(rest_framework.serializers.Serializer):
    additional_days = serializers.IntegerField()

class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer

    @action(detail=True, methods=("POST",), serializer_class=ExtendDueDateSerializer)
    def extend_due_date(self, request, pk=None):
        loan = self.get_object()

        # Validate that the loan is not already overdue.
        if loan.due_date < timezone.now().day():
            raise PermissionDenied("The loan is already overdue.")

        serializer = self.get_serializer()
        serializer.is_valid()

        data = serializer.validated_data
        additional_days = data["additional_days"]

        # Validate that the additional_days is a positive integer.
        if additional_days < 0:
            raise ValidationError("additional_days should be a positive integer")

        # Extend the due_date by the specified number of days.
        loan.due_date = loan.due_date + timedelta(days=additional_days)
        loan.save()

        loan.refresh_from_db()

        # Return the updated loan details in the response.
        return Response({'id': loan.id, "title": loan.book.title, "new_due_date": loan.due_date})
