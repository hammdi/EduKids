"""
Vues pour l'équipement d'accessoires avec IA
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from gamification.models import Accessory, UserAccessory, Avatar
from students.models import Student
from gamification.services import StableDiffusionAPIService
from PIL import Image
import os
import io
from django.conf import settings


@login_required
@require_http_methods(["POST"])
def equip_accessory_manual(request, accessory_id):
    """
    Équipe un accessoire manuellement (sans IA)
    
    POST /api/gamification/equip/<accessory_id>/
    """
    try:
        # Récupérer le profil étudiant
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Profil étudiant non trouvé'
            }, status=404)
        
        # Récupérer l'accessoire
        try:
            accessory = Accessory.objects.get(id=accessory_id, is_active=True)
        except Accessory.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Accessoire non trouvé'
            }, status=404)
        
        # Vérifier que l'étudiant possède cet accessoire
        try:
            student_accessory = UserAccessory.objects.get(
                student=student,
                accessory=accessory
            )
        except UserAccessory.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Tu ne possèdes pas cet accessoire. Achète-le d\'abord !'
            }, status=403)
        
        # Déséquiper les autres accessoires du même type (slot unique)
        UserAccessory.objects.filter(
            student=student,
            accessory__accessory_type=accessory.accessory_type,
            status='equipped'
        ).exclude(id=student_accessory.id).update(status='owned')
        
        # Équiper l'accessoire
        student_accessory.status = 'equipped'
        student_accessory.save()
        
        return JsonResponse({
            'success': True,
            'message': f'✨ {accessory.name} équipé avec succès !',
            'accessory_id': accessory.id,
            'accessory_name': accessory.name,
            'accessory_type': accessory.accessory_type
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def equip_accessory_with_ai(request, accessory_id):
    """
    Équipe un accessoire avec modification IA de l'avatar
    Applique l'accessoire sur l'avatar existant et génère une nouvelle image
    
    POST /api/gamification/equip/<accessory_id>/
    """
    try:
        # Récupérer le profil étudiant
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Profil étudiant non trouvé'
            }, status=404)
        
        # Récupérer l'accessoire
        try:
            accessory = Accessory.objects.get(id=accessory_id, is_active=True)
        except Accessory.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Accessoire non trouvé'
            }, status=404)
        
        # Vérifier que l'étudiant possède cet accessoire
        try:
            student_accessory = UserAccessory.objects.get(
                student=student,
                accessory=accessory
            )
        except UserAccessory.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Tu ne possèdes pas cet accessoire. Achète-le d\'abord !'
            }, status=403)
        
        # Récupérer ou créer l'avatar
        avatar, created = Avatar.objects.get_or_create(
            student=student,
            defaults={'level': 1}
        )
        
        # Vérifier que l'avatar a une image
        if not avatar.image:
            return JsonResponse({
                'success': False,
                'message': 'Veuillez d\'abord uploader une image d\'avatar avant d\'équiper des accessoires.',
                'action': 'upload_avatar_first'
            }, status=400)
        
        # Vérifier que l'accessoire a une image
        if not accessory.image:
            return JsonResponse({
                'success': False,
                'message': 'Cet accessoire n\'a pas d\'image disponible'
            }, status=400)
        
        # Utiliser le service IA Stable Diffusion API pour équiper l'accessoire
        ai_service = StableDiffusionAPIService()
        
        # Charger les images
        from PIL import Image
        
        # Ouvrir l'image de l'avatar
        try:
            # Essayer d'ouvrir le fichier local
            avatar_img = Image.open(avatar.image.path)
        except Exception as e:
            # Si le fichier n'existe pas localement, essayer de le télécharger
            try:
                import requests
                from django.conf import settings
                
                # Construire l'URL complète
                if avatar.image.url.startswith('http'):
                    url = avatar.image.url
                else:
                    # URL relative, ajouter le domaine
                    url = f"http://127.0.0.1:8000{avatar.image.url}"
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                avatar_img = Image.open(io.BytesIO(response.content))
            except Exception as e2:
                return JsonResponse({
                    'success': False,
                    'message': f'Impossible de charger l\'image de l\'avatar: {str(e2)}'
                }, status=500)
        
        # Ouvrir l'image de l'accessoire
        try:
            accessory_img = Image.open(accessory.image.path)
        except Exception as e:
            try:
                import requests
                
                # Construire l'URL complète
                if accessory.image.url.startswith('http'):
                    url = accessory.image.url
                else:
                    url = f"http://127.0.0.1:8000{accessory.image.url}"
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                accessory_img = Image.open(io.BytesIO(response.content))
            except Exception as e2:
                return JsonResponse({
                    'success': False,
                    'message': f'Impossible de charger l\'image de l\'accessoire: {str(e2)}'
                }, status=500)
        
        # Appliquer l'accessoire avec l'IA
        result = ai_service.equip_accessory_with_ai(
            avatar_img,
            accessory_img,
            accessory.accessory_type,
            accessory.name
        )
        
        if not result['success']:
            return JsonResponse({
                'success': False,
                'message': result['message']
            }, status=500)
        
        # Sauvegarder la nouvelle image d'avatar
        import time
        timestamp = int(time.time())
        filename = f'avatar_{student.id}_{accessory_id}_{timestamp}.jpg'
        
        new_avatar_file = ai_service.save_avatar_image(
            result['image'],
            filename=filename
        )
        
        # Mettre à jour l'avatar avec la nouvelle image
        avatar.image.save(
            filename,
            new_avatar_file,
            save=True
        )
        
        # Déséquiper les autres accessoires du même type (un seul par type)
        UserAccessory.objects.filter(
            student=student,
            accessory__accessory_type=accessory.accessory_type,
            status='equipped'
        ).exclude(id=student_accessory.id).update(status='owned')
        
        # Équiper l'accessoire
        student_accessory.status = 'equipped'
        student_accessory.save()
        
        return JsonResponse({
            'success': True,
            'message': result['message'],
            'avatar_url': avatar.image.url,
            'accessory_name': accessory.name,
            'accessory_type': accessory.accessory_type
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Erreur serveur: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def unequip_accessory(request, accessory_id):
    """
    Déséquipe un accessoire ET restaure l'avatar à son état initial
    
    POST /api/gamification/unequip/<accessory_id>/
    """
    try:
        # Récupérer le profil étudiant
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Profil étudiant non trouvé'
            }, status=404)
        
        # Récupérer l'accessoire
        try:
            student_accessory = UserAccessory.objects.get(
                id=accessory_id,
                student=student
            )
        except UserAccessory.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Accessoire non trouvé'
            }, status=404)
        
        # Déséquiper l'accessoire
        student_accessory.status = 'owned'
        student_accessory.save()
        
        # Restaurer l'avatar à son état initial
        try:
            avatar = Avatar.objects.get(student=student)
            
            # Si une image originale existe, la restaurer
            if hasattr(avatar, 'original_image') and avatar.original_image:
                avatar.image = avatar.original_image
                avatar.save()
                
                return JsonResponse({
                    'success': True,
                    'message': '✅ Accessoire retiré et avatar restauré',
                    'accessory_id': student_accessory.accessory.id,
                    'avatar_url': avatar.image.url,
                    'restored': True
                })
        except Avatar.DoesNotExist:
            pass
        
        # Si pas d'avatar original, juste déséquiper
        return JsonResponse({
            'success': True,
            'message': '✅ Accessoire retiré',
            'accessory_id': student_accessory.accessory.id,
            'restored': False
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def restore_original_avatar(request):
    """
    Restaure l'avatar à son état initial (sans accessoires)
    
    POST /api/gamification/restore-avatar/
    """
    try:
        student = Student.objects.get(user=request.user)
        avatar = Avatar.objects.get(student=student)
        
        # Déséquiper tous les accessoires
        UserAccessory.objects.filter(
            student=student,
            status='equipped'
        ).update(status='owned')
        
        # Si un avatar original existe, le restaurer
        if hasattr(avatar, 'original_image') and avatar.original_image:
            avatar.image = avatar.original_image
            avatar.save()
            
            return JsonResponse({
                'success': True,
                'message': '🔄 Avatar restauré à son état initial',
                'avatar_url': avatar.image.url
            })
        else:
            # Pas d'image originale sauvegardée, juste déséquiper
            return JsonResponse({
                'success': True,
                'message': '✅ Tous les accessoires ont été retirés',
                'avatar_url': avatar.image.url if avatar.image else None
            })
            
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Profil étudiant non trouvé'
        }, status=404)
    except Avatar.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Aucun avatar trouvé'
        }, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }, status=500)
