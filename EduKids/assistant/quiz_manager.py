"""Quiz manager: generate quizzes, grade answers, and provide simple explanations.

This module uses the existing Mistral client when available to produce
age-appropriate quizzes. If the LLM is not available, a small deterministic
fallback generator produces simple multiple-choice quizzes.
"""
from typing import List, Dict, Any, Optional
import json
import os
from .mistral_client import get_client


def _fallback_quiz(topic: str, num_questions: int = 3, age: int = 9) -> Dict[str, Any]:
    # Helpful fallback: try to produce sensible local quiz questions for a few
    # common topics (planets, capitales, animaux). If topic is unknown, fall
    # back to a very small templated quiz.
    # Normalize topic string: lowercase, remove surrounding whitespace and
    # try to extract the core topic after common phrases like "quiz sur".
    raw = (topic or '').strip()
    t = raw.lower()
    # Remove common leading phrases that users may send (e.g. "fais-moi un quiz sur ...")
    import re
    m = re.search(r"quiz\s+(?:sur|on)\s+(.+)$", t)
    if m:
        t = m.group(1).strip()
    # Common typo fixes / mappings
    typos = {
        'putter': 'potter',
        'harryputter': 'harry potter',
        'harry_putter': 'harry potter',
    }
    for bad, good in typos.items():
        if bad in t:
            t = t.replace(bad, good)
    questions: List[Dict[str, Any]] = []

    def add(qtext, choices, answer_index=0):
        questions.append({'id': len(questions) + 1, 'question': qtext, 'choices': choices, 'answer_index': answer_index})

    # Planets
    if 'planete' in t or 'planètes' in t or 'planetes' in t:
        pool = [
            ("Quelle est la planète la plus proche du Soleil ?", ["Mercure", "Vénus", "Terre", "Mars"], 0),
            ("Quelle est la plus grande planète du système solaire ?", ["Jupiter", "Saturne", "Uranus", "Neptune"], 0),
            ("Quelle planète est appelée la planète rouge ?", ["Mars", "Vénus", "Mercure", "Terre"], 0),
            ("Quelle planète avons-nous pour vivre ?", ["Terre", "Mars", "Vénus", "Mercure"], 0),
        ]
        for q, ch, ai in pool[:num_questions]:
            add(q, ch, ai)
        return {'title': f'Quiz: {topic}', 'questions': questions}

    # Capitals (simple examples)
    if 'capitale' in t or 'capitale' in t or 'capital' in t or 'france' in t or 'paris' in t:
        pool = [
            ("Quelle est la capitale de la France ?", ["Londres", "Paris", "Berlin", "Rome"], 1),
            ("Quelle est la capitale de l'Italie ?", ["Madrid", "Vienne", "Rome", "Athènes"], 2),
            ("Quelle est la capitale de l'Allemagne ?", ["Berlin", "Zurich", "Munich", "Hambourg"], 0),
        ]
        for q, ch, ai in pool[:num_questions]:
            add(q, ch, ai)
        return {'title': f'Quiz: {topic}', 'questions': questions}

    # Animals / colors simple
    if 'anim' in t or 'animal' in t or 'animaux' in t:
        pool = [
            ("Quel animal est connu pour aboyer ?", ["Chat", "Chien", "Oiseau", "Lapin"], 1),
            ("Quel animal nage et a des nageoires ?", ["Chien", "Oiseau", "Poisson", "Cheval"], 2),
            ("Quel animal est grand et a une trompe ?", ["Éléphant", "Souris", "Chien", "Chat"], 0),
        ]
        for q, ch, ai in pool[:num_questions]:
            add(q, ch, ai)
        return {'title': f'Quiz: {topic}', 'questions': questions}

    # Harry Potter specific questions (accepts 'harry' or 'potter' anywhere)
    if 'harry' in t or 'potter' in t:
        pool = [
            ("Qui est l'auteur des livres Harry Potter ?", ["J. R. R. Tolkien", "J. K. Rowling", "C. S. Lewis", "Roald Dahl"], 1),
            ("Quel est le nom de l'école de magie fréquentée par Harry ?", ["Beauxbâtons", "Poudlard", "Durmstrang", "Ilvermorny"], 1),
            ("Comment s'appelle l'ennemi principal de Harry ?", ["Voldemort", "Dumbledore", "Snape", "Hagrid"], 0),
            ("Quel est le nom de l'ami roux et loyal d'Harry ?", ["Ron Weasley", "Draco Malfoy", "Neville Longbottom", "Severus Snape"], 0),
        ]
        for q, ch, ai in pool[:num_questions]:
            add(q, ch, ai)
        return {'title': f'Quiz: {raw or topic}', 'questions': questions}

    # Simple addition/math quizzes
    if 'addit' in t or 'addition' in t or 'plus' in t or 'somme' in t or 'addition simple' in t:
        # Deterministic simple addition questions for offline testing
        for i in range(num_questions):
            # create increasing difficulty: small sums for first questions
            a = 1 + i + (age // 6)
            b = 2 + i + (age // 7)
            correct = a + b
            # generate distractors (distinct)
            opts = [correct, correct + 1, max(0, correct - 1), correct + 2]
            # ensure all options are unique and convert to strings
            seen = []
            choices = []
            for v in opts:
                if v not in seen:
                    seen.append(v)
                    choices.append(str(v))
            # pad if necessary
            while len(choices) < 4:
                choices.append(str(correct + len(choices)))
            add(f"Quel est le résultat de {a} + {b} ?", choices, 0)
        return {'title': f'Quiz: {raw or topic}', 'questions': questions}

    # Generic templated fallback
    for i in range(num_questions):
        q = {
            'id': i + 1,
            'question': f"Question sur {topic} n°{i+1} : Donne la bonne réponse.",
            'choices': [f"Option {j+1}" for j in range(4)],
            'answer_index': 0,
        }
        questions.append(q)
    return {'title': f'Quiz: {topic}', 'questions': questions}


def generate_quiz(topic: str, difficulty: str = 'easy', num_questions: int = 3, age: int = 9) -> Dict[str, Any]:
    """Generate a quiz for the given topic.

    Attempts to use the Mistral client for better results. Returns a dict with
    keys: title, questions (list of {id, question, choices, answer_index}).
    """
    # Sanitize inputs
    num_questions = max(1, min(5, int(num_questions)))
    try:
        client = get_client()
    except Exception:
        return _fallback_quiz(topic, num_questions, age)

    # We'll try the LLM a couple of times with a strict JSON instruction, otherwise fallback
    import re
    placeholder_pattern = re.compile(r"^\s*option\s*\d+\s*$", re.IGNORECASE)

    llm_attempts = 2
    system_msg = 'Tu es un assistant qui renvoie STRICTEMENT un objet JSON valide, sans texte additionnel.'
    user_msg = (
        "Génère un quiz pour des enfants (6-12 ans) au format JSON strict. "
        "Structure exacte attendue: {\n  \"title\": string,\n  \"questions\": [ { \"id\": int, \"question\": string, \"choices\": [string,...], \"answer_index\": int }, ... ]\n}."
        f" Sujet: {topic}. Difficulté: {difficulty}. Age: {age}. Nombre de questions: {num_questions}."
        "Les champs doivent être présents et `answer_index` doit être un entier 0-based valide pour chaque question."
        "Retourne uniquement l'objet JSON sans explications ni commentaires."
    )

    for _ in range(llm_attempts):
        try:
            chunks = list(client.stream_generate(user_msg, system=system_msg, language='fr'))
            text = ''.join(chunks).strip()

            try:
                quiz = json.loads(text)
            except Exception:
                m = re.search(r"\{[\s\S]*\}", text)
                if m:
                    quiz = json.loads(m.group(0))
                else:
                    raise

            # Validate basic structure
            qlist = quiz.get('questions') if isinstance(quiz, dict) else None
            if not isinstance(qlist, list) or len(qlist) == 0:
                raise ValueError('no questions')

            normalized_questions = []
            saw_placeholder = False
            for i, qq in enumerate(qlist):
                if not isinstance(qq, dict):
                    raise ValueError('question not object')
                qtext = qq.get('question') or qq.get('text') or ''
                choices = qq.get('choices') or qq.get('options') or []
                if not isinstance(choices, list) or len(choices) < 2:
                    raise ValueError('not enough choices')
                choices = [str(c).strip() for c in choices]
                if all(placeholder_pattern.match(c) for c in choices):
                    saw_placeholder = True
                ai = None
                for key in ('answer_index', 'correct_index', 'answer'):
                    if key in qq:
                        try:
                            ai = int(qq.get(key))
                            break
                        except Exception:
                            ai = None

                # Accept either 0-based or 1-based indices from LLM output. If ai is within 1..len(choices), convert to 0-based.
                if ai is not None:
                    try:
                        if ai >= 1 and ai <= len(choices):
                            ai = ai - 1
                    except Exception:
                        pass

                if ai is None or not (0 <= ai < len(choices)):
                    raise ValueError('invalid answer_index')
                normalized_questions.append({'id': qq.get('id') or (i + 1), 'question': qtext, 'choices': choices, 'answer_index': ai})

            if saw_placeholder:
                raise ValueError('placeholder choices')

            def _clean_topic(t: str) -> str:
                if not t:
                    return 'Général'
                tt = t.strip()
                tt = re.sub(r"(?i)^(?:fais[- ]?moi\s+un\s+quiz(?:\s+sur|\s+de)?|génère(?:r)?\s+un\s+quiz(?:\s+sur|\s+de)?|donne[- ]?moi\s+un\s+quiz(?:\s+sur|\s+de)?|je\s+veux\s+un\s+quiz(?:\s+sur|\s+de)?)", "", tt)
                tt = tt.strip(' :,-')
                tt = tt[:40].strip()
                return tt.capitalize() if tt else 'Général'

            title = f"Quiz: {_clean_topic(topic or quiz.get('title') or '')}"
            return {'title': title, 'questions': normalized_questions}

        except Exception:
            # try again
            continue

    # if all LLM attempts fail, return deterministic fallback
    return _fallback_quiz(topic, num_questions, age)


def grade_quiz(quiz: Dict[str, Any], answers: Dict[str, int]) -> Dict[str, Any]:
    """Grade answers and return simple explanations for wrong answers.

    answers: mapping of question id (as str or int) -> chosen index
    Returns: { total, correct, details: [ {id, correct_index, user_index, is_correct, explanation} ] }
    """
    total = len(quiz.get('questions', []))
    correct = 0
    details = []
    for q in quiz.get('questions', []):
        qid = q.get('id')
        ai = q.get('answer_index')
        ui = answers.get(str(qid), answers.get(qid))
        try:
            ui = int(ui) if ui is not None else None
        except Exception:
            ui = None
        choices = q.get('choices', []) or []
        ok = (ui is not None and ai == ui)
        if ok:
            correct += 1
            explanation = 'Bonne réponse ! Bravo 😊'
        else:
            # Friendly child-oriented explanation: mention correct choice text
            correct_text = q.get('choices', [])[ai] if isinstance(q.get('choices'), list) and ai < len(q.get('choices')) else 'la bonne réponse'
            # Optionally ask Mistral for a nicer explanation when configured
            explanation = None
            try:
                if os.environ.get('MISTRAL_API_KEY') and os.environ.get('MISTRAL_USE_FOR_GRADING', '1') == '1':
                    client = get_client()
                    if ui is not None and 0 <= ui < len(choices):
                        prompt = (
                            f"Explique de façon simple et encourageante à un enfant de 6 à 12 ans pourquoi la réponse correcte est '{correct_text}' "
                            f"pour la question: {q.get('question')}. L'élève a répondu: {choices[ui]}. Sois bref et positif."
                        )
                    else:
                        prompt = (
                            f"Explique de façon simple et encourageante à un enfant de 6 à 12 ans pourquoi la réponse correcte est '{correct_text}' pour la question: {q.get('question')}."
                        )
                    chunks = list(client.stream_generate(prompt, system='Tu es un professeur pour les enfants; sois bref, clair et positif.', language='fr'))
                    explanation = ''.join(chunks).strip()
                    if not explanation:
                        explanation = None
            except Exception:
                explanation = None
            if not explanation:
                explanation = f"Ce n'est pas tout à fait ça. La bonne réponse est: {correct_text}. Petit rappel: essaie de relire la question et de choisir la réponse la plus simple."
        details.append({'id': qid, 'correct_index': ai, 'user_index': ui, 'is_correct': ok, 'explanation': explanation})
    return {'total': total, 'correct': correct, 'details': details}


def grade_answer(quiz: Dict[str, Any], qid: int, user_input: str) -> Dict[str, Any]:
    """Grade a single answer provided as text. Returns dict with keys:
       { id, correct_index, user_index, is_correct, explanation }

    user_input: can be an index (1-based) or the text of one of the choices.
    """
    q = None
    for qq in quiz.get('questions', []):
        if qq.get('id') == qid:
            q = qq
            break
    if not q:
        return {'id': qid, 'error': 'question not found'}

    ai = q.get('answer_index')
    choices = q.get('choices', []) or []

    # Try parse as 1-based index
    ui = None
    if user_input is None:
        ui = None
    else:
        s = str(user_input).strip()
        # digit? allow '1' .. '4'
        if s.isdigit():
            try:
                v = int(s)
                # Accept both 1-based (user typed 1..n) and 0-based (client sent 0..n-1).
                # Prefer 1-based when in range 1..len(choices).
                if v >= 1 and v <= len(choices):
                    ui = v - 1
                elif v >= 0 and v < len(choices):
                    ui = v
                else:
                    ui = None
            except Exception:
                ui = None
        else:
            # match against choices ignoring case and punctuation
            import re
            def norm(x):
                return re.sub(r"[^a-z0-9]+", "", (x or '').lower())
            ns = norm(s)
            for idx, ch in enumerate(choices):
                if norm(ch) == ns:
                    ui = idx
                    break

    ok = (ui is not None and ai == ui)
    if ok:
        explanation = 'Bonne réponse ! Bravo 🎉'
    else:
        correct_text = choices[ai] if ai is not None and ai < len(choices) else 'la bonne réponse'
        # Optionally ask Mistral for an explanation
        explanation = None
        try:
            if os.environ.get('MISTRAL_API_KEY') and os.environ.get('MISTRAL_USE_FOR_GRADING', '1') == '1':
                client = get_client()
                prompt = (
                    f"Explique brièvement à un enfant pourquoi la bonne réponse est '{correct_text}' pour la question: {q.get('question')}. "
                    f"L'élève a répondu: {user_input}. Sois encourageant et fais court."
                )
                chunks = list(client.stream_generate(prompt, system='Tu es un professeur pour enfants; réponds en français, phrases courtes.', language='fr'))
                explanation = ''.join(chunks).strip()
                if not explanation:
                    explanation = None
        except Exception:
            explanation = None
        if not explanation:
            explanation = f"Ce n'est pas tout à fait ça. La bonne réponse est: {correct_text}. Continue comme ça, tu apprends en t'amusant ! 😊"

    return {'id': qid, 'correct_index': ai, 'user_index': ui, 'is_correct': ok, 'explanation': explanation}
