"""
Service IA pour modifier les avatars avec Stable Diffusion API (Automatic1111)
Remplace HuggingFace Diffusers par une solution API plus légère et rapide
"""
import os
import io
import base64
import requests
from PIL import Image, ImageDraw
import numpy as np
from django.conf import settings
from django.core.files.base import ContentFile


class StableDiffusionAPIService:
    """
    Service pour modifier les avatars avec Stable Diffusion API (Automatic1111)
    """
    
    def __init__(self):
        """Initialiser le service avec l'API Stable Diffusion"""
        # URL de l'API Stable Diffusion (Automatic1111)
        self.api_url = getattr(
            settings, 
            'SD_API_URL', 
            os.getenv('SD_API_URL', 'http://127.0.0.1:7860')
        )
        
        # Token API (optionnel)
        self.api_token = getattr(
            settings, 
            'SD_API_TOKEN', 
            os.getenv('SD_API_TOKEN', None)
        )
        
        # Vérifier si l'API est disponible
        self.api_available = self._check_api_availability()
        
        if self.api_available:
            print(f"✅ Stable Diffusion API disponible: {self.api_url}")
        else:
            print(f"⚠️ Stable Diffusion API non disponible. Utilisation du fallback PIL.")
    
    def _check_api_availability(self):
        """Vérifie si l'API Stable Diffusion est disponible"""
        try:
            response = requests.get(
                f"{self.api_url}/sdapi/v1/sd-models",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"⚠️ API SD non disponible: {e}")
            return False
    
    def equip_accessory_with_ai(self, avatar_image, accessory_image, accessory_type, accessory_name):
        """
        Applique un accessoire sur l'avatar avec Stable Diffusion API
        
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
            
            # Essayer d'utiliser Stable Diffusion API
            if self.api_available:
                result = self._apply_with_sd_api(
                    avatar_img, accessory_img, accessory_type, accessory_name
                )
                if result['success']:
                    return result
            
            # Fallback: Utiliser PIL (composite simple)
            print("⚠️ Utilisation du fallback PIL (pas d'API SD)")
            result = self._composite_images(avatar_img, accessory_img, accessory_type)
            
            if result['success']:
                return {
                    'success': True,
                    'image': result['image'],
                    'message': self._get_success_message(accessory_name)
                }
            else:
                return result
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'image': None,
                'message': f"Erreur lors de l'application de l'accessoire: {str(e)}"
            }
    
    def _apply_with_sd_api(self, avatar_img, accessory_img, accessory_type, accessory_name):
        """
        Applique l'accessoire avec Stable Diffusion API (Inpainting)
        """
        try:
            # Redimensionner l'avatar à 512x512 (optimal pour SD)
            avatar_resized = avatar_img.resize((512, 512), Image.Resampling.LANCZOS)
            
            # Créer un masque pour la zone où appliquer l'accessoire
            mask = self._create_mask(accessory_type, (512, 512))
            
            # Convertir les images en base64
            avatar_b64 = self._image_to_base64(avatar_resized)
            mask_b64 = self._image_to_base64(mask)
            
            # Créer le prompt selon le type d'accessoire
            prompt = self._generate_inpainting_prompt(accessory_type, accessory_name)
            negative_prompt = "blurry, low quality, distorted, ugly, deformed"
            
            # Préparer la requête pour l'API
            payload = {
                "init_images": [avatar_b64],
                "mask": mask_b64,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "steps": 20,
                "cfg_scale": 7.5,
                "width": 512,
                "height": 512,
                "denoising_strength": 0.75,
                "inpainting_fill": 1,  # Original
                "inpaint_full_res": False,
                "sampler_name": "DPM++ 2M Karras"
            }
            
            # Headers
            headers = {"Content-Type": "application/json"}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            
            # Appeler l'API
            response = requests.post(
                f"{self.api_url}/sdapi/v1/img2img",
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
            
            # Récupérer l'image générée
            result_data = response.json()
            result_b64 = result_data['images'][0]
            
            # Décoder l'image
            result_img = self._base64_to_image(result_b64)
            
            # Redimensionner au format original
            result_img = result_img.resize(avatar_img.size, Image.Resampling.LANCZOS)
            
            return {
                'success': True,
                'image': result_img,
                'message': f'✨ {accessory_name} appliqué avec IA !'
            }
            
        except Exception as e:
            print(f"❌ Erreur SD API: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'image': None,
                'message': str(e)
            }
    
    def _create_mask(self, accessory_type, size):
        """
        Crée un masque pour l'inpainting selon le type d'accessoire
        Blanc = zone à modifier, Noir = zone à conserver
        """
        width, height = size
        mask = Image.new('RGB', size, (0, 0, 0))  # Noir = ne pas modifier
        draw = ImageDraw.Draw(mask)
        
        if accessory_type == 'head':
            # Zone du haut (chapeau, casque)
            draw.ellipse([width*0.2, 0, width*0.8, height*0.3], fill=(255, 255, 255))
        
        elif accessory_type == 'body':
            # Zone du corps (vêtement)
            draw.rectangle([width*0.1, height*0.25, width*0.9, height*0.75], fill=(255, 255, 255))
        
        elif accessory_type == 'tool':
            # Zone à droite (outil dans la main)
            draw.ellipse([width*0.6, height*0.3, width*0.95, height*0.7], fill=(255, 255, 255))
        
        else:
            # Zone centrale par défaut
            draw.ellipse([width*0.25, height*0.25, width*0.75, height*0.75], fill=(255, 255, 255))
        
        return mask
    
    def _generate_inpainting_prompt(self, accessory_type, accessory_name):
        """Générer un prompt pour l'inpainting"""
        prompts = {
            'head': f"person wearing {accessory_name} on head, cartoon style, colorful, high quality, detailed",
            'body': f"person wearing {accessory_name}, cartoon style, colorful, high quality, detailed",
            'tool': f"person holding {accessory_name}, cartoon style, colorful, high quality, detailed",
            'default': f"person with {accessory_name}, cartoon style, colorful, high quality, detailed"
        }
        
        return prompts.get(accessory_type, prompts['default'])
    
    def _composite_images(self, avatar_img, accessory_img, accessory_type):
        """
        Fallback: Composite l'accessoire sur l'avatar avec PIL (pas d'IA)
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
                new_width = int(avatar_width * 0.6)
                new_height = int(accessory_img.height * (new_width / accessory_img.width))
                accessory_resized = accessory_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                x = (avatar_width - new_width) // 2
                y = int(avatar_height * 0.05)
                
            elif accessory_type == 'body':
                new_width = int(avatar_width * 0.8)
                new_height = int(accessory_img.height * (new_width / accessory_img.width))
                accessory_resized = accessory_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                x = (avatar_width - new_width) // 2
                y = int(avatar_height * 0.25)
                
            elif accessory_type == 'tool':
                new_width = int(avatar_width * 0.45)
                new_height = int(accessory_img.height * (new_width / accessory_img.width))
                accessory_resized = accessory_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                x = int(avatar_width * 0.55)
                y = int(avatar_height * 0.35)
                
            else:
                new_width = int(avatar_width * 0.5)
                new_height = int(accessory_img.height * (new_width / accessory_img.width))
                accessory_resized = accessory_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                x = (avatar_width - new_width) // 2
                y = (avatar_height - new_height) // 2
            
            # S'assurer que l'accessoire ne dépasse pas
            if x + new_width > avatar_width:
                x = avatar_width - new_width
            if y + new_height > avatar_height:
                y = avatar_height - new_height
            if x < 0:
                x = 0
            if y < 0:
                y = 0
            
            # Composite avec transparence
            result_img.paste(accessory_resized, (x, y), accessory_resized)
            
            # Convertir en RGB pour JPEG
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
    
    def _image_to_base64(self, pil_image):
        """Convertit une PIL Image en base64 pour l'API"""
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')
    
    def _base64_to_image(self, base64_string):
        """Convertit une string base64 en PIL Image"""
        image_data = base64.b64decode(base64_string)
        return Image.open(io.BytesIO(image_data))
    
    def _get_success_message(self, accessory_name):
        """Messages de succès motivants"""
        messages = [
            f"🎉 {accessory_name} équipé avec style !",
            f"✨ Ton avatar adore ce {accessory_name} !",
            f"🌟 Magnifique ! {accessory_name} te va à merveille !",
            f"🎨 Super travail avec {accessory_name} !",
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
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=95)
        buffer.seek(0)
        return ContentFile(buffer.read(), name=filename)
    
    def image_to_base64_response(self, pil_image):
        """
        Convertit une PIL Image en base64 pour la réponse JSON
        
        Returns:
            str: Image encodée en base64
        """
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=95)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')
