from rest_framework import serializers
from core.model.credentials_model import Credentials

class CredentialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Credentials
        fields = ['id', 'access_key', 'secret_key', 'storage']
        extra_kwargs = {'secret_key': {'write_only': True}}

    def create(self, validated_data):
        """Override create to hash secret_key before saving."""
        secret_key = validated_data.pop('secret_key')
        credentials = Credentials(**validated_data)
        credentials.set_secret_key(secret_key)
        credentials.save()
        return credentials




class CredentialUpdateSerializer(serializers.ModelSerializer):
    secret_key = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Credentials
        fields = ['id' , 'access_key', 'secret_key', 'storage']

    def update(self, instance, validated_data):
        if 'secret_key' in validated_data:
            instance.set_secret_key(validated_data.pop('secret_key'))

        return super().update(instance, validated_data)

