from django.core.management.base import BaseCommand
from assistant.models import Conversation, Message

class Command(BaseCommand):
    help = "Backfill Conversation.topic based on first student message or title keywords"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Do not save changes, only report counts')
        parser.add_argument('--limit', type=int, default=0, help='Limit number of conversations to process (0 = all)')

    def handle(self, *args, **options):
        dry = options['dry_run']
        limit = options['limit']
        qs = Conversation.objects.all().order_by('id')
        if limit:
            qs = qs[:limit]
        updated = 0
        total = 0
        for conv in qs:
            total += 1
            topic = self.classify(conv)
            if topic and topic != conv.topic:
                self.stdout.write(f"Conv {conv.id}: {conv.topic} -> {topic}")
                if not dry:
                    conv.topic = topic
                    conv.save(update_fields=['topic'])
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Processed: {total}, Updated: {updated}, Dry-run: {dry}"))

    def classify(self, conv: Conversation) -> str:
        # Prefer first student message, otherwise use title
        first_student_msg = (
            Message.objects.filter(conversation=conv, sender_type='student')
            .order_by('created_at')
            .first()
        )
        text = ''
        if first_student_msg:
            text = (first_student_msg.content or '').strip()
        elif conv.title:
            text = conv.title.strip()
        return self._classify_topic(text)

    def _classify_topic(self, text: str) -> str:
        if not text:
            return 'general'
        t = text.lower()
        if any(k in t for k in ['français', 'francais', 'lecture', 'orthographe', 'grammaire', 'conjugaison', 'vocabulaire']):
            return 'francais'
        if any(k in t for k in ['math', 'calcul', 'addition', 'soustraction', 'multiplication', 'division', 'nombre', 'fraction', 'géométrie', 'geometrie']):
            return 'mathematiques'
        if any(k in t for k in ['science', 'corps', 'plantes', 'animaux', 'énergie', 'energie', 'matière', 'matiere']):
            return 'sciences'
        if any(k in t for k in ['histoire', 'roi', 'reine', 'guerre', 'révolution', 'revolution']):
            return 'histoire'
        if any(k in t for k in ['géographie', 'geographie', 'pays', 'capitale', 'carte', 'continent']):
            return 'geographie'
        return 'general'
