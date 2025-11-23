from rest_framework import serializers
from .models import Cat, Mission, Target
import requests

CAT_API_URL = "https://api.thecatapi.com/v1/breeds"

def validate_cat_breed_sync(breed_name):
    try:
        response = requests.get(CAT_API_URL, timeout=5)
        response.raise_for_status()
        breeds = response.json()
        breed_found = any(
            b['name'].lower() == breed_name.lower() for b in breeds
        )

        if not breed_found:
            raise serializers.ValidationError(
                f"Breed '{breed_name}' is not recognized by TheCatAPI. Please check the spelling."
            )

    except requests.exceptions.RequestException as e:
        raise serializers.ValidationError("Cannot connect to external CatAPI for breed validation.")

class TargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = ['id', 'name', 'country', 'notes', 'is_completed']
        read_only_fields = ['id', 'is_completed']

class MissionSerializer(serializers.ModelSerializer):
    targets = TargetSerializer(many=True)

    class Meta:
        model = Mission
        fields = ['id', 'cat', 'is_completed', 'targets']
        read_only_fields = ['id', 'is_completed']

    def validate_targets(self, targets):
        if not 1 <= len(targets) <= 3:
            raise serializers.ValidationError("A mission must have between 1 and 3 targets.")
        return targets

    def create(self, validated_data):
        targets_data = validated_data.pop('targets')
        mission = Mission.objects.create(**validated_data)
        for target_data in targets_data:
            Target.objects.create(mission=mission, **target_data)
        return mission

class CatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cat
        fields = ['id', 'name', 'experience_years', 'breed', 'salary', 'is_available']
        read_only_fields = ['id', 'is_available', 'name', 'experience_years', 'breed']

    def validate_breed(self, value):
        validate_cat_breed_sync(value)
        return value

class TargetUpdateNotesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = ['notes']