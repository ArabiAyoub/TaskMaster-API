from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, Category, TaskHistory
from django.utils import timezone

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'user']
        read_only_fields = ['user']

class TaskSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        allow_null=True,
        required=False
    )

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'due_date', 'priority', 'status',
                  'created_at', 'updated_at', 'completed_at', 'category', 'category_id',
                  'is_recurring', 'recurrence_interval', 'recurrence_end_date']
        read_only_fields = ['created_at', 'updated_at', 'completed_at']

    def validate_due_date(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Due date must be in the future.")
        return value

    def validate_category_id(self, value):
        if value and value.user != self.context['request'].user:
            raise serializers.ValidationError("Invalid category for this user.")
        return value

class TaskHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskHistory
        fields = ['id', 'old_status', 'new_status', 'changed_at', 'changed_by']