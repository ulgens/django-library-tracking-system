from celery import shared_task
from django.utils import timezone

from .models import Loan
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_loan_notification(loan_id):
    try:
        loan = Loan.objects.get(id=loan_id)
        member_email = loan.member.user.email
        book_title = loan.book.title
        send_mail(
            subject='Book Loaned Successfully',
            message=f'Hello {loan.member.user.username},\n\nYou have successfully loaned "{book_title}".\nPlease return it by the due date.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member_email],
            fail_silently=False,
        )
    except Loan.DoesNotExist:
        pass

@shared_task()
def check_overdue_loans():
    print("Checking overdue loans...")
    overdue_loans = Loan.objects.filter(
        is_returned=False,
        due_date__lt=timezone.now().date(),
    )

    print(f"{overdue_loans.count()} overdue loans found.")

    for loan in overdue_loans.iterator():
        print(loan.id)
        print(loan.book.title)

        member_email = loan.member.user.email
        book_title = loan.book.title
        send_mail(
            subject='You have an overdue loan!',
            message=f'Hello {loan.member.user.username},\n\nYou have an overdue loan for "{book_title}".\nPlease return it immediately.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member_email],
            fail_silently=False,
        )
