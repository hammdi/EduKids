"""
Décorateurs pour l'espace Student - EduKids
Vérification stricte du rôle Student
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def student_required(view_func):
    """
    Décorateur pour restreindre l'accès aux Students uniquement.
    
    Vérifie que :
    1. L'utilisateur est authentifié
    2. L'utilisateur a le rôle 'student'
    3. L'utilisateur a un profil student_profile
    
    Redirige vers la page d'accueil si les conditions ne sont pas remplies.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Vérifier l'authentification
        if not request.user.is_authenticated:
            messages.warning(request, "Connecte-toi pour accéder à ton espace !")
            return redirect('login')
        
        # Vérifier le rôle Student
        if request.user.user_type != 'student':
            messages.error(request, "Cette page est réservée aux élèves uniquement.")
            return redirect('home')
        
        # Vérifier l'existence du profil student
        if not hasattr(request.user, 'student_profile'):
            messages.error(request, "Aucun profil élève trouvé. Contacte un administrateur.")
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
