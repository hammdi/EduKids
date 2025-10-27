"""
Sérialiseurs pour l'API gamification - EduKids

Phase 3 : Avatars & Personnalisation avancée
"""
from rest_framework import serializers
from .models import Badge, UserBadge, Mission, UserMission, Avatar, Accessory, UserAccessory


class AvatarSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les avatars personnalisés
    """
    image_url = serializers.SerializerMethodField()
    equipped_accessories = serializers.SerializerMethodField()
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)

    class Meta:
        model = Avatar
        fields = [
            'id', 'student', 'student_name', 'image', 'image_url',
            'level', 'equipped_accessories', 'created_at', 'updated_at'
        ]
        read_only_fields = ['student', 'created_at', 'updated_at']

    def get_image_url(self, obj):
        """
        Retourne l'URL complète de l'image d'avatar
        """
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_equipped_accessories(self, obj):
        """
        Retourne les accessoires équipés avec leurs détails
        """
        equipped = obj.get_equipped_accessories_by_type()
        result = {}
        for acc_type, accessory in equipped.items():
            result[acc_type] = {
                'id': accessory.id,
                'name': accessory.name,
                'image_url': self._get_accessory_image_url(accessory),
                'type': accessory.accessory_type,
                'type_display': accessory.get_accessory_type_display()
            }
        return result

    def _get_accessory_image_url(self, accessory):
        """
        Helper pour obtenir l'URL de l'image d'accessoire
        """
        if accessory.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(accessory.image.url)
            return accessory.image.url
        return None


class AccessorySerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les accessoires
    """
    image_url = serializers.SerializerMethodField()
    type_display = serializers.CharField(source='get_accessory_type_display', read_only=True)
    owned_by_user = serializers.SerializerMethodField()
    equipped_by_user = serializers.SerializerMethodField()

    class Meta:
        model = Accessory
        fields = [
            'id', 'name', 'image', 'image_url', 'accessory_type', 'type_display',
            'points_required', 'is_active', 'created_at',
            'owned_by_user', 'equipped_by_user'
        ]

    def get_image_url(self, obj):
        """
        Retourne l'URL complète de l'image
        """
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_owned_by_user(self, obj):
        """
        Vérifie si l'utilisateur possède cet accessoire
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserAccessory.objects.filter(
                student__user=request.user,
                accessory=obj,
                status__in=['owned', 'equipped']
            ).exists()
        return False

    def get_equipped_by_user(self, obj):
        """
        Vérifie si l'utilisateur a équipé cet accessoire
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserAccessory.objects.filter(
                student__user=request.user,
                accessory=obj,
                status='equipped'
            ).exists()
        return False


class UserAccessorySerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les accessoires des utilisateurs
    """
    accessory = AccessorySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)

    class Meta:
        model = UserAccessory
        fields = [
            'id', 'student', 'student_name', 'accessory', 'status',
            'status_display', 'date_obtained'
        ]
        read_only_fields = ['student', 'date_obtained']


class AvatarUploadSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'upload d'avatar
    """
    class Meta:
        model = Avatar
        fields = ['image']

    def update(self, instance, validated_data):
        """
        Met à jour seulement l'image et updated_at
        """
        instance.image = validated_data.get('image', instance.image)
        instance.updated_at = serializers.timezone.now()
        instance.save()
        return instance


class AccessoryPurchaseSerializer(serializers.Serializer):
    """
    Sérialiseur pour l'achat d'accessoires
    """
    accessory_id = serializers.IntegerField()

    def validate_accessory_id(self, value):
        """
        Valide que l'accessoire existe et est disponible
        """
        try:
            accessory = Accessory.objects.get(id=value, is_active=True)
            return value
        except Accessory.DoesNotExist:
            raise serializers.ValidationError("Accessoire non trouvé ou indisponible.")


class AccessoryEquipSerializer(serializers.Serializer):
    """
    Sérialiseur pour l'équipement d'accessoires
    """
    accessory_id = serializers.IntegerField()

    def validate_accessory_id(self, value):
        """
        Valide que l'accessoire est possédé par l'utilisateur
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if not UserAccessory.objects.filter(
                student__user=request.user,
                accessory_id=value,
                status='owned'
            ).exists():
                raise serializers.ValidationError("Vous ne possédez pas cet accessoire.")
        return value


# Sérialiseurs existants pour compatibilité
class MissionSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les missions
    """
    type_mission_display = serializers.CharField(
        source='get_type_mission_display',
        read_only=True
    )

    class Meta:
        model = Mission
        fields = [
            'id', 'titre', 'description', 'type_mission', 'type_mission_display',
            'objectif', 'points', 'date_expiration', 'actif', 'created_at'
        ]


class UserMissionSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les missions des utilisateurs
    """
    mission = MissionSerializer(read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display',
        read_only=True
    )

    class Meta:
        model = UserMission
        fields = [
            'id', 'user', 'mission', 'progression', 'statut', 'statut_display',
            'date_attribuee', 'date_terminee'
        ]
        read_only_fields = ['user', 'date_attribuee', 'date_terminee']


class BadgeSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les badges
    """
    class Meta:
        model = Badge
        fields = [
            'id', 'nom', 'description', 'icon', 'condition',
            'points_bonus', 'is_active', 'created_at'
        ]


class UserBadgeSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les badges des utilisateurs
    """
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = UserBadge
        fields = ['id', 'user', 'badge', 'date_obtention']
        read_only_fields = ['user', 'date_obtention']