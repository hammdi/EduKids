"""
Service IA pour modifier les avatars avec HuggingFace Stable Diffusion Inpainting
Remplace l'utilisation de Gemini par une solution plus adaptée
"""
import os
import io
import base64
from PIL import Image, ImageDraw
import numpy as np
from django.conf import settings
from django.core.files.base import ContentFile

# Import conditionnel pour éviter les erreurs si les packages ne sont pas installés
try:
    from diffusers import StableDiffusionInpaintPipeline
    import torch
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    print("⚠️ Diffusers non disponible. Installation: pip install diffusers transformers torch")


class HuggingFaceAvatarService:
    """
    Service pour modifier les avatars avec Stable Diffusion Inpainting
    """
    
    def __init__(self):
        """Initialiser le service avec HuggingFace"""
        self.pipeline = None
        self.device = "cpu"  # Par défaut CPU, utiliser "cuda" si GPU disponible
        
        # Vérifier si diffusers est disponible
        if not DIFFUSERS_AVAILABLE:
            print("⚠️ Mode fallback: Utilisation de PIL uniquement (pas d'IA)")
            return
        
        # Vérifier si un GPU est disponible
        if torch.cuda.is_available():
            self.device = "cuda"
            print("✅ GPU détecté, utilisation de CUDA")
        else:
            print("⚠️ Pas de GPU, utilisation du CPU (plus lent)")
        
        # Token HuggingFace (optionnel, pour les modèles privés)
        self.hf_token = getattr(settings, 'HUGGINGFACE_TOKEN', os.getenv('HUGGINGFACE_TOKEN'))
        
        # Ne pas charger le modèle au démarrage (trop lourd)
        # On le chargera à la demande
        print("✅ HuggingFaceAvatarService initialisé (modèle non chargé)")
    
    def _load_pipeline(self):
        """Charge le pipeline Stable Diffusion Inpainting (lazy loading)"""
        if self.pipeline is not None:
            return True
        
        if not DIFFUSERS_AVAILABLE:
            return False
        
        try:
            print("🔄 Chargement du modèle Stable Diffusion Inpainting...")
            
            # Utiliser un modèle léger et rapide
            model_id = "runwayml/stable-diffusion-inpainting"
            
            self.pipeline = StableDiffusionInpaintPipeline.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                use_auth_token=self.hf_token if self.hf_token else None
            )
            
            self.pipeline = self.pipeline.to(self.device)
            
            # Optimisations pour économiser la mémoire
            if self.device == "cuda":
                self.pipeline.enable_attention_slicing()
            
            print("✅ Modèle Stable Diffusion chargé avec succès")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement du modèle: {e}")
            self.pipeline = None
            return False
    
    def equip_accessory_with_ai(self, avatar_image, accessory_image, accessory_type, accessory_name):
        """
        Applique un accessoire sur l'avatar avec IA (Stable Diffusion Inpainting)
        
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
            
            # Essayer d'utiliser Stable Diffusion Inpainting
            if DIFFUSERS_AVAILABLE and self._load_pipeline():
                result = self._apply_with_inpainting(
                    avatar_img, accessory_img, accessory_type, accessory_name
                )
                if result['success']:
                    return result
            
            # Fallback: Utiliser PIL (composite simple)
            print("⚠️ Utilisation du fallback PIL (pas d'IA)")
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
    
    def _apply_with_inpainting(self, avatar_img, accessory_img, accessory_type, accessory_name):
        """
        Applique l'accessoire avec Stable Diffusion Inpainting
        """
        try:
            # Redimensionner l'avatar à 512x512 (taille optimale pour SD)
            avatar_resized = avatar_img.resize((512, 512), Image.Resampling.LANCZOS)
            
            # Créer un masque pour la zone où appliquer l'accessoire
            mask = self._create_mask(accessory_type, (512, 512))
            
            # Créer le prompt selon le type d'accessoire
            prompt = self._generate_inpainting_prompt(accessory_type, accessory_name)
            
            # Appliquer l'inpainting
            result_img = self.pipeline(
                prompt=prompt,
                image=avatar_resized,
                mask_image=mask,
                num_inference_steps=20,  # Moins d'étapes = plus rapide
                guidance_scale=7.5,
                height=512,
                width=512
            ).images[0]
            
            # Redimensionner au format original
            result_img = result_img.resize(avatar_img.size, Image.Resampling.LANCZOS)
            
            return {
                'success': True,
                'image': result_img,
                'message': f'✨ {accessory_name} appliqué avec IA !'
            }
            
        except Exception as e:
            print(f"❌ Erreur inpainting: {e}")
            return {
                'success': False,
                'image': None,
                'message': str(e)
            }
    
    def _create_mask(self, accessory_type, size):
        """
        Crée un masque pour l'inpainting selon le type d'accessoire
        """
        width, height = size
        mask = Image.new('L', size, 0)  # Noir = ne pas modifier
        draw = ImageDraw.Draw(mask)
        
        if accessory_type == 'head':
            # Zone du haut (chapeau, casque)
            draw.ellipse([width*0.2, 0, width*0.8, height*0.3], fill=255)
        
        elif accessory_type == 'body':
            # Zone du corps (vêtement)
            draw.rectangle([width*0.1, height*0.25, width*0.9, height*0.75], fill=255)
        
        elif accessory_type == 'tool':
            # Zone à droite (outil dans la main)
            draw.ellipse([width*0.6, height*0.3, width*0.95, height*0.7], fill=255)
        
        else:
            # Zone centrale par défaut
            draw.ellipse([width*0.25, height*0.25, width*0.75, height*0.75], fill=255)
        
        return mask
    
    def _generate_inpainting_prompt(self, accessory_type, accessory_name):
        """Générer un prompt pour l'inpainting"""
        prompts = {
            'head': f"a person wearing a {accessory_name} on their head, cartoon style, colorful, high quality",
            'body': f"a person wearing a {accessory_name}, cartoon style, colorful, high quality",
            'tool': f"a person holding a {accessory_name}, cartoon style, colorful, high quality",
            'default': f"a person with a {accessory_name}, cartoon style, colorful, high quality"
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
    
    def image_to_base64(self, pil_image):
        """
        Convertit une PIL Image en base64
        
        Returns:
            str: Image encodée en base64
        """
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=95)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')
