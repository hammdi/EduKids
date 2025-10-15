"""
Views pour les évaluations, incluant l'évaluation vocale par IA
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from students.models import Student
from .voice_models import VoiceAssessment
from .voice_analyzer import VoiceAnalyzer


@login_required
def voice_assessment(request):
    """Voice assessment interface"""
    return render(request, 'assessments/voice_assessment.html')

@login_required
def teacher_assessments(request):
    """Teacher assessments view"""
    return render(request, 'teachers/assessments.html')

@login_required
def student_exercises(request):
    """Student exercises view"""
    return render(request, 'students/exercises.html')

@login_required
def teacher_exercises(request):
    """Teacher exercises view"""
    return render(request, 'teachers/exercises.html')

@login_required
def voice_assessment_view(request, student_id=None):
    """
    Interface d'évaluation vocale
    """
    # Si pas de student_id, utiliser l'utilisateur connecté
    if student_id:
        student = get_object_or_404(Student, id=student_id)
    else:
        # Récupérer le profil étudiant de l'utilisateur connecté
        try:
            student = request.user.student_profile
        except:
            return redirect('admin:index')  # Rediriger si pas un étudiant
    
    # Question par défaut (peut être passée en paramètre)
    prompt = request.GET.get('prompt', 
        "Raconte-moi ce que tu as appris aujourd'hui en classe.")
    
    context = {
        'student': student,
        'prompt': prompt,
    }
    
    return render(request, 'assessments/voice_assessment.html', context)


@require_http_methods(["POST"])
def voice_assessment_analyze(request):
    """
    API endpoint pour analyser un enregistrement vocal
    """
    try:
        # Récupérer les données
        audio_file = request.FILES.get('audio')
        prompt = request.POST.get('prompt')
        student_id = request.POST.get('student_id')
        
        if not all([audio_file, prompt, student_id]):
            return JsonResponse({
                'error': 'Données manquantes'
            }, status=400)
        
        student = get_object_or_404(Student, id=student_id)
        
        # Créer l'évaluation
        assessment = VoiceAssessment.objects.create(
            student=student,
            prompt=prompt,
            audio_file=audio_file,
            status='processing'
        )
        
        # TODO: Intégrer Speech-to-Text API (OpenAI Whisper)
        # Pour l'instant, simulation avec transcription factice
        transcription = "Ceci est une transcription de démonstration. L'élève a parlé avec clarté et structure."
        assessment.transcription = transcription
        
        # Analyser avec l'IA
        analyzer = VoiceAnalyzer()
        results = analyzer.analyze_complete(
            audio_path=assessment.audio_file.path,
            transcription=transcription,
            prompt=prompt
        )
        
        # Sauvegarder les résultats
        assessment.originality_score = results['scores']['originality_score']
        assessment.verbal_structure_score = results['scores']['verbal_structure_score']
        assessment.verbal_fluency_score = results['scores']['verbal_fluency_score']
        assessment.verbal_vocabulary_score = results['scores']['verbal_vocabulary_score']
        assessment.paraverbal_intonation_score = results['scores']['paraverbal_intonation_score']
        assessment.paraverbal_rhythm_score = results['scores']['paraverbal_rhythm_score']
        assessment.paraverbal_timing_score = results['scores']['paraverbal_timing_score']
        
        assessment.originality_analysis = results['originality_analysis']
        assessment.verbal_analysis = results['verbal_analysis']
        assessment.paraverbal_analysis = results['paraverbal_analysis']
        assessment.ai_feedback = results['feedback']
        
        # Calculer le score global
        assessment.calculate_overall_score()
        assessment.status = 'completed'
        assessment.save()
        
        # Préparer la réponse
        strengths_weaknesses = assessment.get_strengths_weaknesses()
        
        response_data = {
            'id': assessment.id,
            'overall_score': assessment.overall_score,
            'grade_letter': assessment.get_grade_letter(),
            'originality_score': assessment.originality_score,
            'verbal_structure_score': assessment.verbal_structure_score,
            'verbal_fluency_score': assessment.verbal_fluency_score,
            'verbal_vocabulary_score': assessment.verbal_vocabulary_score,
            'paraverbal_intonation_score': assessment.paraverbal_intonation_score,
            'paraverbal_rhythm_score': assessment.paraverbal_rhythm_score,
            'paraverbal_timing_score': assessment.paraverbal_timing_score,
            'ai_feedback': assessment.ai_feedback,
            'strengths': strengths_weaknesses['strengths'],
            'weaknesses': strengths_weaknesses['weaknesses'],
            'transcription': transcription
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@login_required
def voice_assessment_results(request, assessment_id):
    """
    Afficher les résultats d'une évaluation vocale
    """
    assessment = get_object_or_404(VoiceAssessment, id=assessment_id)
    
    # Vérifier les permissions
    if request.user.user_type not in ['admin', 'teacher'] and \
       assessment.student.user != request.user:
        return redirect('admin:index')
    
    strengths_weaknesses = assessment.get_strengths_weaknesses()
    
    context = {
        'assessment': assessment,
        'strengths': strengths_weaknesses['strengths'],
        'weaknesses': strengths_weaknesses['weaknesses'],
    }
    
    return render(request, 'assessments/voice_results.html', context)


@login_required
def voice_assessment_history(request, student_id=None):
    """
    Historique des évaluations vocales d'un élève
    """
    if student_id:
        student = get_object_or_404(Student, id=student_id)
    else:
        try:
            student = request.user.student_profile
        except:
            return redirect('admin:index')
    
    assessments = VoiceAssessment.objects.filter(
        student=student
    ).order_by('-created_at')
    
    context = {
        'student': student,
        'assessments': assessments,
    }
    
    return render(request, 'assessments/voice_history.html', context)
