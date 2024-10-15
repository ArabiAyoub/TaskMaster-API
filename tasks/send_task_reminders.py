from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from tasks.models import Task

class Command(BaseCommand):
    help = 'Sends email reminders for tasks due soon'

    def handle(self, *args, **options):
        tomorrow = timezone.now() + timezone.timedelta(days=1)
        due_tasks = Task.objects.filter(due_date__date=tomorrow.date(), status='PENDING')

        for task in due_tasks:
            send_mail(
                'Task Reminder',
                f'Your task "{task.title}" is due tomorrow!',
                'from@example.com',
                [task.user.email],
                fail_silently=False,
            )

        self.stdout.write(self.style.SUCCESS(f'Sent {due_tasks.count()} reminders'))