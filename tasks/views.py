# views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Task, Category
from .serializers import TaskSerializer, UserSerializer, CategorySerializer, TaskHistorySerializer
from django.contrib.auth.models import User
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

class CategoryViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'category']
    ordering_fields = ['due_date', 'priority']

    def get_queryset(self):
        queryset = Task.objects.filter(user=self.request.user)
        due_date = self.request.query_params.get('due_date', None)
        if due_date:
            queryset = queryset.filter(due_date__date=due_date)
        return queryset

    def perform_create(self, serializer):
        category_id = self.request.data.get('category')
        if category_id:
            category = Category.objects.filter(id=category_id, user=self.request.user).first()
            if category:
                serializer.save(user=self.request.user, category=category)
            else:
                raise serializers.ValidationError("Invalid category for this user.")
        else:
            serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        category_id = self.request.data.get('category')
        if category_id:
            category = Category.objects.filter(id=category_id, user=self.request.user).first()
            if category:
                serializer.save(category=category)
            else:
                raise serializers.ValidationError("Invalid category for this user.")
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        task = self.get_object()
        if task.status == 'COMPLETED':
            return Response({"detail": "Task is already completed."}, status=status.HTTP_400_BAD_REQUEST)
        task.mark_complete()
        return Response({"detail": "Task marked as complete."})

    @action(detail=True, methods=['post'])
    def mark_incomplete(self, request, pk=None):
        task = self.get_object()
        if task.status == 'PENDING':
            return Response({"detail": "Task is already pending."}, status=status.HTTP_400_BAD_REQUEST)
        task.mark_incomplete()
        return Response({"detail": "Task marked as incomplete."})

    @action(detail=False, methods=['get'])
    def completed(self, request):
        completed_tasks = self.get_queryset().filter(status='COMPLETED')
        page = self.paginate_queryset(completed_tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(completed_tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        task = self.get_object()
        history = task.history.all().order_by('-changed_at')
        serializer = TaskHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        upcoming_tasks = self.get_queryset().filter(
            Q(due_date__gte=timezone.now()) | Q(is_recurring=True),
            status='PENDING'
        ).order_by('due_date')
        page = self.paginate_queryset(upcoming_tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(upcoming_tasks, many=True)
        return Response(serializer.data)