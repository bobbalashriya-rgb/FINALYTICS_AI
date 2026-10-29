from rest_framework import serializers
from companies.models import Company


class CompanySerializer(serializers.ModelSerializer):
    """
    Serializer for Indian listed company profile information.
    """
    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "ticker",
            "slug",
            "bse_code",
            "source_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
