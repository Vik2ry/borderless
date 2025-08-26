from accounts.models import User
from rest_framework import serializers

class RegisterSerializer(serializers.ModelSerializer):
    handle = serializers.CharField(source="username")  # alias for username
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'handle', 'email', 'password', 'date_joined']
        read_only_fields = ['id', 'date_joined']
        extra_kwargs = {'password': {'write_only': True}}
    def validate_handle(self, value):
        if User.objects.filter(handle=value).exists():
            raise serializers.ValidationError("A user with that handle already exists.")
        return value
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value


    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    handle = serializers.CharField(source="username")

    class Meta:
        model = User
        fields = ('id', 'handle', 'created_at')
        read_only_fields = ('id', 'created_at')
