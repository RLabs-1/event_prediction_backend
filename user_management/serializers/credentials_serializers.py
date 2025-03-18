from rest_framework import serializers
from core.model.credentials_model import Credentials




class CredentialUpdateSerializer(serializers.ModelSerializer):
    secret_key = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Credentials
        fields = ['id' , 'access_key', 'secret_key', 'storage']

    def update(self, instance, validated_data):
        if 'secret_key' in validated_data:
            instance.set_secret_key(validated_data.pop('secret_key'))

        return super().update(instance, validated_data)

