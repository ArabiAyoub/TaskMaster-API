from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')

    def __str__(self):
        return self.name

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()
    priority = models.CharField(max_length=6, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=9, choices=STATUS_CHOICES, default='PENDING')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    is_recurring = models.BooleanField(default=False)
    recurrence_interval = models.PositiveIntegerField(null=True, blank=True)  # in days
    recurrence_end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    def mark_complete(self):
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()
        TaskHistory.objects.create(task=self, old_status='PENDING', new_status='COMPLETED', changed_by=self.user)

    def mark_incomplete(self):
        self.status = 'PENDING'
        self.completed_at = None
        self.save()
        TaskHistory.objects.create(task=self, old_status='COMPLETED', new_status='PENDING', changed_by=self.user)

class TaskHistory(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='history')
    old_status = models.CharField(max_length=9, choices=Task.STATUS_CHOICES)
    new_status = models.CharField(max_length=9, choices=Task.STATUS_CHOICES)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.task.title}: {self.old_status} -> {self.new_status}"