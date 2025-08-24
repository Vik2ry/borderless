from accounts.models import User
from rest_framework import serializers

class RegisterSerializer(serializers.ModelSerializer):
    handle = serializers.CharField(source="username")  # alias for username
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('handle', 'password')

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
