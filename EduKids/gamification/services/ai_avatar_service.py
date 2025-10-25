"""
Service IA pour modifier les avatars avec Gemini API
"""
import os
import base64
import requests
import io
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
import google.generativeai as genai


class AIAvatarService:
    """
    Service pour modifier les avatars avec l'IA Gemini
    """
    
    def __init__(self):
        """Initialiser le service avec la clé API Gemini"""
        api_key = getattr(settings, 'GEMINI_API_KEY', os.getenv('GEMINI_API_KEY'))
        if not api_key:
            # Pas d'API key : utiliser uniquement PIL (pas d'erreur)
            self.model = None
            return
        
        genai.configure(api_key=api_key)
        
        # Essayer les modèles dans l'ordre de préférence
        # Note: Pour l'instant, on utilise uniquement PIL car Gemini ne génère pas d'images
        # On garde le code pour une future intégration avec un modèle de génération d'images
        self.model = None
        
        # Modèles à essayer (commentés pour l'instant)
        # models_to_try = [
        #     'gemini-1.5-pro-latest',
        #     'gemini-1.5-pro',
        #     'gemini-pro',
        #     'gemini-pro-vision'
        # ]
        # 
        # for model_name in models_to_try:
        #     try:
        #         self.model = genai.GenerativeModel(model_name)
        #         print(f"✅ Modèle Gemini initialisé: {model_name}")
        #         break
        #     except Exception as e:
        #         print(f"⚠️ Modèle {model_name} non disponible: {e}")
        #         continue
    
    def equip_accessory_with_ai(self, avatar_image, accessory_image, accessory_type, accessory_name):
        """
        Utilise Gemini pour équiper un accessoire sur l'avatar
        
        Args:
            avatar_image: Image de l'avatar (PIL Image ou path)
            accessory_image: Image de l'accessoire (PIL Image ou path)
            accessory_type: Type d'accessoire (head, body, tool, etc.)
            accessory_name: Nom de l'accessoire
            
        Returns:
            dict: {
                'success': bool,
                'image': PIL Image ou None,
                'message': str
            }
        """
        try:
            # Charger les images si ce sont des paths
            if isinstance(avatar_image, str):
                avatar_img = Image.open(avatar_image)
            else:
                avatar_img = avatar_image
            
            if isinstance(accessory_image, str):
                accessory_img = Image.open(accessory_image)
            else:
                accessory_img = accessory_image
            
            # Convertir en RGB si nécessaire
            if avatar_img.mode != 'RGB':
                avatar_img = avatar_img.convert('RGB')
            if accessory_img.mode != 'RGBA':
                accessory_img = accessory_img.convert('RGBA')
            
            # Préparer le prompt selon le type d'accessoire
            prompt = self._generate_prompt(accessory_type, accessory_name)
            
            # Appeler Gemini avec les images
            response = self.model.generate_content([
                prompt,
                avatar_img,
                accessory_img
            ])
            
            # Note: Gemini ne peut pas générer d'images directement
            # On va utiliser une approche alternative avec PIL
            result = self._composite_images(avatar_img, accessory_img, accessory_type)
            
            if result['success']:
                return {
                    'success': True,
                    'image': result['image'],
                    'message': self._get_success_message(accessory_name)
                }
            else:
                return {
                    'success': False,
                    'image': None,
                    'message': result['message']
                }
                
        except Exception as e:
            return {
                'success': False,
                'image': None,
                'message': f"L'IA a rencontré un problème: {str(e)}"
            }
    
    def _composite_images(self, avatar_img, accessory_img, accessory_type):
        """
        Composite l'accessoire sur l'avatar selon le type
        Applique l'accessoire de manière réaliste avec gestion de la transparence
        """
        try:
            # Créer une copie de l'avatar en RGBA
            if avatar_img.mode != 'RGBA':
                result_img = avatar_img.convert('RGBA')
            else:
                result_img = avatar_img.copy()
            
            # S'assurer que l'accessoire est en RGBA
            if accessory_img.mode != 'RGBA':
                accessory_img = accessory_img.convert('RGBA')
            
            # Redimensionner l'accessoire selon le type
            avatar_width, avatar_height = result_img.size
            
            if accessory_type == 'head':
                # Chapeau/casque: 60% de la largeur, positionné en haut
                new_width = int(avatar_width * 0.6)
                new_height = int(accessory_img.height * (new_width / accessory_img.width))
                accessory_resized = accessory_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Position: centré horizontalement, 5% du haut (plus visible)
                x = (avatar_width - new_width) // 2
                y = int(avatar_height * 0.05)
                
            elif accessory_type == 'body':
                # Vêtement: 80% de la largeur, centré
                new_width = int(avatar_width * 0.8)
                new_height = int(accessory_img.height * (new_width / accessory_img.width))
                accessory_resized = accessory_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                x = (avatar_width - new_width) // 2
                y = int(avatar_height * 0.25)
                
            elif accessory_type == 'tool':
                # Outil: 45% de la largeur, à droite
                new_width = int(avatar_width * 0.45)
                new_height = int(accessory_img.height * (new_width / accessory_img.width))
                accessory_resized = accessory_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                x = int(avatar_width * 0.55)
                y = int(avatar_height * 0.35)
                
            else:
                # Par défaut: 50% de la largeur, centré
                new_width = int(avatar_width * 0.5)
                new_height = int(accessory_img.height * (new_width / accessory_img.width))
                accessory_resized = accessory_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                x = (avatar_width - new_width) // 2
                y = (avatar_height - new_height) // 2
            
            # S'assurer que l'accessoire ne dépasse pas les limites
            if x + new_width > avatar_width:
                x = avatar_width - new_width
            if y + new_height > avatar_height:
                y = avatar_height - new_height
            if x < 0:
                x = 0
            if y < 0:
                y = 0
            
            # Composite l'accessoire sur l'avatar avec gestion de la transparence
            # Utiliser le canal alpha de l'accessoire comme masque
            result_img.paste(accessory_resized, (x, y), accessory_resized)
            
            # Convertir en RGB pour sauvegarder en JPEG (meilleure compatibilité)
            final_img = Image.new('RGB', result_img.size, (255, 255, 255))
            final_img.paste(result_img, mask=result_img.split()[3] if result_img.mode == 'RGBA' else None)
            
            return {
                'success': True,
                'image': final_img,
                'message': 'Accessoire équipé avec succès!'
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'image': None,
                'message': f"Erreur lors du composite: {str(e)}"
            }
    
    def _generate_prompt(self, accessory_type, accessory_name):
        """Générer un prompt adapté au type d'accessoire"""
        prompts = {
            'head': f"Positionne ce {accessory_name} sur la tête de l'avatar de manière naturelle et esthétique.",
            'body': f"Habille l'avatar avec ce {accessory_name} de manière cohérente.",
            'tool': f"Place cet outil {accessory_name} dans la main droite de l'avatar.",
            'default': f"Intègre cet accessoire {accessory_name} de manière harmonieuse sur l'avatar."
        }
        
        base_prompt = prompts.get(accessory_type, prompts['default'])
        
        return f"""
        Tu es un artiste de jeu vidéo spécialisé dans les avatars cartoon.
        
        {base_prompt}
        
        Règles importantes:
        - Ne déforme pas l'avatar original
        - Garde un style cartoon cohérent
        - L'accessoire doit être bien visible
        - Respecte les proportions naturelles
        - Le résultat doit être fun et motivant pour un enfant
        
        Retourne une image composite de haute qualité.
        """
    
    def _get_success_message(self, accessory_name):
        """Messages de succès motivants"""
        messages = [
            f"🎉 {accessory_name} équipé avec style !",
            f"✨ Ton avatar adore ce {accessory_name} !",
            f"🌟 Magnifique ! {accessory_name} te va à merveille !",
            f"🎨 L'IA a fait un super travail avec {accessory_name} !",
            f"🚀 Ton avatar est encore plus cool avec {accessory_name} !",
        ]
        import random
        return random.choice(messages)
    
    def save_avatar_image(self, pil_image, filename='avatar.jpg'):
        """
        Convertit une PIL Image en Django File
        
        Returns:
            ContentFile prêt à être sauvegardé dans un ImageField
        """
        # Créer un buffer en mémoire
        buffer = io.BytesIO()
        
        # Sauvegarder l'image dans le buffer
        pil_image.save(buffer, format='JPEG', quality=95)
        buffer.seek(0)
        
        # Créer un ContentFile
        return ContentFile(buffer.read(), name=filename)
