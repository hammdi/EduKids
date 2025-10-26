"""Helpers for image and PDF generation with optional external API integration.

Functions:
 - generate_image(prompt, width=800, height=600) -> bytes (PNG)
 - generate_pdf(title, paragraphs) -> bytes (PDF)

If an external image API is configured (env IMAGE_API_KEY and IMAGE_API_URL), the
function will try to call it; otherwise it falls back to a simple PIL-based image.
"""
import os
from io import BytesIO


def generate_image(prompt: str, width: int = 800, height: int = 600) -> bytes:
    """Return PNG bytes for the requested prompt.

    If an external API is configured via IMAGE_API_KEY, IMAGE_API_URL it will be
    called. Otherwise a simple placeholder image using PIL is returned.
    """
    # Try provider-specific image APIs if configured (Mistral preferred if available)
    # 0) Mistral image endpoint (if configured)
    mistral_key = os.environ.get('MISTRAL_API_KEY')
    mistral_img_url = os.environ.get('MISTRAL_IMAGE_URL')
    if mistral_key and mistral_img_url:
        try:
            import requests, base64
            headers = {'Authorization': f'Bearer {mistral_key}', 'Content-Type': 'application/json'}
            payload = {'prompt': prompt, 'width': width, 'height': height}
            resp = requests.post(mistral_img_url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            # Accept JSON { 'b64_json': '...' } or direct bytes
            ctype = resp.headers.get('Content-Type', '')
            if 'application/json' in ctype:
                try:
                    j = resp.json()
                    # common fields: b64_json or data[0].b64_json or base64
                    if isinstance(j, dict) and j.get('b64_json'):
                        return base64.b64decode(j.get('b64_json'))
                    if isinstance(j, dict) and j.get('base64'):
                        return base64.b64decode(j.get('base64'))
                    if isinstance(j, dict) and 'data' in j and isinstance(j['data'], list) and j['data'] and j['data'][0].get('b64_json'):
                        return base64.b64decode(j['data'][0].get('b64_json'))
                except Exception:
                    pass
            # fallback: return raw content bytes
            return resp.content
        except Exception:
            pass

    # Next: OpenAI if configured
    # 1) OpenAI Images API (uses OPENAI_API_KEY)
    openai_key = os.environ.get('OPENAI_API_KEY')
    if openai_key:
        try:
            import requests, base64
            oa_url = os.environ.get('OPENAI_IMAGE_URL', 'https://api.openai.com/v1/images/generations')
            # Choose a reasonable size (OpenAI expects sizes like '1024x1024')
            size_map = {256: '256x256', 512: '512x512', 768: '768x768', 800: '1024x1024', 1024: '1024x1024'}
            size_str = size_map.get(width, '1024x1024')
            payload = {'prompt': prompt, 'n': 1, 'size': size_str}
            headers = {'Authorization': f'Bearer {openai_key}', 'Content-Type': 'application/json'}
            resp = requests.post(oa_url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            # OpenAI may return base64 in data[0].b64_json or a URL in data[0].url
            if isinstance(data, dict) and 'data' in data and len(data['data']) > 0:
                item = data['data'][0]
                if 'b64_json' in item:
                    img_b64 = item['b64_json']
                    return base64.b64decode(img_b64)
                elif 'url' in item:
                    # fetch the image bytes
                    url = item['url']
                    r2 = requests.get(url, timeout=30)
                    r2.raise_for_status()
                    return r2.content
            # if unexpected shape, fall through to generic handler
        except Exception:
            pass

    # 2) Generic external API (IMAGE_API_URL + IMAGE_API_KEY) — keep for backward compatibility
    api_key = os.environ.get('IMAGE_API_KEY')
    api_url = os.environ.get('IMAGE_API_URL')
    if api_key and api_url:
        try:
            import requests
            resp = requests.post(api_url, json={'prompt': prompt, 'width': width, 'height': height}, headers={'Authorization': f'Bearer {api_key}'}, timeout=30)
            resp.raise_for_status()
            # Accept either direct bytes or a JSON with base64
            ctype = resp.headers.get('Content-Type', '')
            if 'application/json' in ctype:
                try:
                    j = resp.json()
                    if isinstance(j, dict) and j.get('base64'):
                        import base64 as _b64
                        return _b64.b64decode(j.get('base64'))
                    if isinstance(j, dict) and j.get('b64'):
                        import base64 as _b64
                        return _b64.b64decode(j.get('b64'))
                except Exception:
                    pass
            return resp.content
        except Exception:
            # fall back to PIL below
            pass

    # Fallback simple image (try to create a colored illustrative scene from the prompt)
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        raise RuntimeError('Pillow is required for image fallback generation')

    img = Image.new('RGB', (width, height), color=(250, 248, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('arial.ttf', 36)
    except Exception:
        font = ImageFont.load_default()

    # Try to produce a simple representational scene when prompt mentions common objects
    text = prompt or 'EduKids'
    lp = (text or '').lower()
    made_scene = False
    try:
        # simple elephant + book scene
        if 'éléphant' in lp or 'elephant' in lp:
            made_scene = True
            # background sky
            draw.rectangle([0, 0, width, int(height * 0.6)], fill=(180, 220, 255))
            # ground
            draw.rectangle([0, int(height * 0.6), width, height], fill=(200, 230, 180))
            # body (oval)
            bx = int(width * 0.25)
            by = int(height * 0.45)
            bw = int(width * 0.4)
            bh = int(height * 0.25)
            draw.ellipse([bx, by, bx + bw, by + bh], fill=(160, 160, 190), outline=(120, 120, 140))
            # head
            hx = bx + int(bw * 0.7)
            hy = by - int(bh * 0.25)
            draw.ellipse([hx, hy, hx + int(bw * 0.5), hy + int(bh * 0.6)], fill=(160, 160, 190), outline=(120, 120, 140))
            # trunk
            tx1 = hx + int(bw * 0.4)
            ty1 = hy + int(bh * 0.3)
            draw.line([tx1, ty1, tx1 + 80, ty1 + 40], fill=(140, 140, 170), width=18)
            # eye
            draw.ellipse([hx + 20, hy + 20, hx + 28, hy + 28], fill=(0, 0, 0))
            # book in front
            book_x = bx + 40
            book_y = by + int(bh * 0.5)
            bwid = 140
            bheight = 100
            draw.rectangle([book_x, book_y, book_x + bwid, book_y + bheight], fill=(255, 245, 180), outline=(200, 160, 90))
            # book lines
            for i in range(5):
                y = book_y + 10 + i * 16
                draw.line([book_x + 10, y, book_x + bwid - 10, y], fill=(150, 120, 80), width=2)
            # caption text
            try:
                cap_font = ImageFont.truetype('arial.ttf', 20)
            except Exception:
                cap_font = ImageFont.load_default()
            caption = 'Un éléphant qui lit un livre' if 'fr' in lp or 'éléphant' in lp else 'An elephant reading a book'
            draw.text((20, 20), caption, fill=(40, 40, 40), font=cap_font)

        # add more simple object scenes as needed (sun, tree)
        if not made_scene:
            # generic colorful placeholder: gradient + simple centered illustration
            for i in range(height):
                r = int(255 - (i / height) * 60)
                g = int(245 - (i / height) * 20)
                b = int(255 - (i / height) * 80)
                draw.line([(0, i), (width, i)], fill=(r, g, b))
            # simple rounded rectangle in center with an icon-like circle
            cx = width // 2
            cy = height // 2
            draw.ellipse([cx - 120, cy - 120, cx + 120, cy + 120], fill=(255, 255, 255), outline=(220, 220, 220))
            try:
                icon_font = ImageFont.truetype('arial.ttf', 40)
            except Exception:
                icon_font = ImageFont.load_default()
            # center the prompt text inside the circle
            made_scene = True
            # measure text size
            try:
                if hasattr(draw, 'textbbox'):
                    bbox = draw.textbbox((0, 0), text, font=icon_font)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                else:
                    tw, th = draw.textsize(text, font=icon_font)
            except Exception:
                tw = len(text) * 8
                th = 20
            draw.text((cx - tw // 2, cy - th // 2), text, fill=(40, 40, 40), font=icon_font)
    except Exception:
        # If scene drawing fails for any reason, fall back to simple text overlay
        made_scene = False

    # If we didn't create a scene above, fall back to centered text
    if not made_scene:
        # Measure text size: use textbbox when available (Pillow >=8), fallback to textsize
        try:
            if hasattr(draw, 'textbbox'):
                bbox = draw.textbbox((0, 0), text, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
            else:
                # Some Pillow builds may not have draw.textsize; try font measurements
                if hasattr(draw, 'textsize'):
                    tw, th = draw.textsize(text, font=font)
                elif hasattr(font, 'getbbox'):
                    bbox = font.getbbox(text)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                elif hasattr(font, 'getsize'):
                    tw, th = font.getsize(text)
                else:
                    raise RuntimeError('Cannot measure text size: Pillow methods unavailable')
        except Exception:
            # As a final fallback, approximate text size
            tw = len(text) * (font.size if hasattr(font, 'size') else 10)
            th = (font.size if hasattr(font, 'size') else 10) + 8

        draw.text(((width - tw) / 2, (height - th) / 2), text, fill=(60, 60, 60), font=font)
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def create_thumbnail(image_bytes: bytes, size=(320, 200)) -> bytes:
    """Return thumbnail JPEG bytes for given image bytes."""
    try:
        from PIL import Image
    except Exception:
        raise RuntimeError('Pillow is required for thumbnail generation')

    buf = BytesIO(image_bytes)
    img = Image.open(buf)
    img.thumbnail(size)
    out = BytesIO()
    img.save(out, format='JPEG', quality=85)
    return out.getvalue()


def generate_pdf(title: str, paragraphs) -> bytes:
    """Return PDF bytes for title and paragraphs.

    Creates a colorful, kid-friendly PDF with pastel colors, icons, and clear structure.
    Uses reportlab if available.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.units import inch
        from reportlab.platypus.flowables import Flowable
    except Exception:
        raise RuntimeError('reportlab is required for PDF generation')

    # Kid-friendly pastel color palette
    PASTEL_COLORS = {
        'pink': colors.HexColor('#FFD6E8'),
        'blue': colors.HexColor('#D6E8FF'),
        'yellow': colors.HexColor('#FFF9D6'),
        'green': colors.HexColor('#D6FFE8'),
        'purple': colors.HexColor('#E8D6FF'),
        'peach': colors.HexColor('#FFE8D6'),
        'mint': colors.HexColor('#D6FFF0'),
        'lavender': colors.HexColor('#F0E8FF'),
    }
    
    # Header/accent colors (slightly darker but still soft)
    ACCENT_COLORS = {
        'pink': colors.HexColor('#FFB3D9'),
        'blue': colors.HexColor('#B3D9FF'),
        'yellow': colors.HexColor('#FFF0B3'),
        'green': colors.HexColor('#B3FFD9'),
        'purple': colors.HexColor('#D9B3FF'),
    }

    # Custom flowable for decorative star/icon
    class StarIcon(Flowable):
        def __init__(self, x=0, y=0, size=12, color=colors.HexColor('#FFD700')):
            Flowable.__init__(self)
            self.x = x
            self.y = y
            self.size = size
            self.color = color
            self.width = size
            self.height = size

        def draw(self):
            c = self.canv
            c.setFillColor(self.color)
            # Simple star shape (5-pointed)
            from math import cos, sin, pi
            points = []
            for i in range(10):
                angle = pi / 2 + (2 * pi * i / 10)
                r = self.size / 2 if i % 2 == 0 else self.size / 4
                points.append((self.x + r * cos(angle), self.y + r * sin(angle)))
            p = c.beginPath()
            p.moveTo(*points[0])
            for pt in points[1:]:
                p.lineTo(*pt)
            p.close()
            c.drawPath(p, fill=1)

    # Build the PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        leftMargin=40, 
        rightMargin=40, 
        topMargin=50, 
        bottomMargin=50
    )
    width, height = A4
    content_width = width - 80  # accounting for margins

    styles = getSampleStyleSheet()
    
    # Enhanced styles for kids
    title_style = ParagraphStyle(
        'KidTitle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        fontSize=28,
        textColor=colors.HexColor('#FF6B9D'),  # Soft pink
        spaceAfter=20,
        spaceBefore=10,
        leading=32,
    )
    
    subtitle_style = ParagraphStyle(
        'KidSubtitle',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#7B68EE'),  # Medium purple
        spaceAfter=16,
        leading=18,
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=colors.HexColor('#4A90E2'),  # Soft blue
        spaceAfter=8,
        spaceBefore=12,
        leftIndent=10,
    )
    
    body_style = ParagraphStyle(
        'KidBody',
        parent=styles['BodyText'],
        alignment=TA_LEFT,
        fontName='Helvetica',
        fontSize=13,
        leading=20,
        textColor=colors.HexColor('#2C3E50'),  # Dark gray-blue
        leftIndent=15,
        rightIndent=15,
        spaceAfter=6,
    )
    
    question_style = ParagraphStyle(
        'Question',
        parent=styles['BodyText'],
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=18,
        textColor=colors.HexColor('#E85D75'),  # Coral pink
        leftIndent=20,
        spaceAfter=8,
        spaceBefore=8,
    )
    
    option_style = ParagraphStyle(
        'Option',
        parent=styles['BodyText'],
        alignment=TA_LEFT,
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#34495E'),
        leftIndent=35,
        spaceAfter=4,
    )
    
    footer_style = ParagraphStyle(
        'KidFooter',
        parent=styles['Italic'],
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique',
        fontSize=11,
        textColor=colors.HexColor('#7F8C8D'),
        spaceAfter=10,
    )

    flowables = []

    # ========== DECORATIVE HEADER SECTION ==========
    # Create a colorful header with rounded-corner effect using nested tables
    
    # Main title with emoji decoration
    emoji_title = f"✨ {title or 'EduKids Document'} ✨"
    title_para = Paragraph(emoji_title, title_style)
    
    # Subtitle with date
    from datetime import datetime
    date_str = datetime.now().strftime('%d/%m/%Y')
    subtitle_text = f"📚 Document créé le {date_str} 📚"
    subtitle_para = Paragraph(subtitle_text, subtitle_style)
    
    # Create header table with gradient-like effect (multiple colored rows)
    header_table = Table(
        [[title_para], [subtitle_para]], 
        colWidths=[content_width],
        rowHeights=[50, 30]
    )
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PASTEL_COLORS['pink']),
        ('BACKGROUND', (0, 1), (-1, 1), PASTEL_COLORS['purple']),
        ('ROUNDEDCORNERS', [10, 10, 10, 10]),
        ('BOX', (0, 0), (-1, -1), 2, ACCENT_COLORS['pink']),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    flowables.append(header_table)
    flowables.append(Spacer(1, 20))

    # ========== CONTENT SECTION ==========
    if not paragraphs:
        paragraphs = ['Aucun contenu disponible.']

    # Detect if this is a quiz (contains "Question" patterns)
    is_quiz = any('question' in str(p).lower() or 'options:' in str(p).lower() for p in paragraphs)
    
    if is_quiz:
        # ========== QUIZ FORMAT ==========
        flowables.append(Paragraph("🎯 Quiz Éducatif", section_title_style))
        flowables.append(Spacer(1, 10))
        
        question_num = 0
        current_question = None
        color_index = 0
        color_list = ['blue', 'green', 'yellow', 'purple', 'peach', 'mint']
        
        for idx, p in enumerate(paragraphs):
            text = (p or '').strip()
            if not text or text.lower().startswith('quiz'):
                continue
            
            # Detect question vs options
            if text.lower().startswith('question'):
                # Save previous question if exists
                if current_question:
                    flowables.append(Spacer(1, 12))
                
                question_num += 1
                # Extract question text
                q_text = text.split(':', 1)[1].strip() if ':' in text else text
                
                # Create question card with icon
                q_icon = f"❓ Question {question_num}"
                q_header = Paragraph(q_icon, question_style)
                q_body = Paragraph(q_text, body_style)
                
                # Color-coded question box
                bg_color = PASTEL_COLORS[color_list[color_index % len(color_list)]]
                border_color = ACCENT_COLORS[color_list[color_index % len(color_list)]]
                color_index += 1
                
                question_table = Table(
                    [[q_header], [q_body]], 
                    colWidths=[content_width - 40],
                    rowHeights=[25, None]
                )
                question_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), border_color),
                    ('BACKGROUND', (0, 1), (-1, 1), bg_color),
                    ('BOX', (0, 0), (-1, -1), 1.5, border_color),
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.white),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ]))
                flowables.append(question_table)
                flowables.append(Spacer(1, 8))
                current_question = question_num
                
            elif text.lower().startswith('options:'):
                # Parse options
                options_text = text.split(':', 1)[1].strip() if ':' in text else text
                options = [opt.strip() for opt in options_text.split(';') if opt.strip()]
                
                # Create options list with checkboxes
                for opt in options:
                    opt_text = f"☐  {opt}"
                    opt_para = Paragraph(opt_text, option_style)
                    
                    # Light colored option boxes
                    opt_table = Table(
                        [[opt_para]], 
                        colWidths=[content_width - 60]
                    )
                    opt_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FAFAFA')),
                        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ]))
                    flowables.append(opt_table)
                    flowables.append(Spacer(1, 4))
            else:
                # Regular paragraph in quiz context
                para = Paragraph(text, body_style)
                flowables.append(para)
                flowables.append(Spacer(1, 6))
    
    else:
        # ========== REGULAR CONTENT FORMAT ==========
        flowables.append(Paragraph("📖 Contenu", section_title_style))
        flowables.append(Spacer(1, 10))
        
        color_list = ['blue', 'green', 'yellow', 'purple', 'mint', 'lavender']
        
        for idx, p in enumerate(paragraphs):
            text = (p or '').strip()
            if not text:
                continue
            
            # Split long paragraphs into sentences for better readability
            sentences = [s.strip() for s in text.replace('! ', '!|').replace('? ', '?|').replace('. ', '.|').split('|') if s.strip()]
            
            for sent_idx, sentence in enumerate(sentences):
                if not sentence:
                    continue
                
                # Add period if missing
                if not sentence[-1] in '.!?':
                    sentence += '.'
                
                # Alternate icons for variety
                icons = ['🌟', '✨', '💡', '🎨', '🚀', '🌈', '⭐', '🎯']
                icon = icons[(idx + sent_idx) % len(icons)]
                
                para_text = f"{icon}  {sentence}"
                para = Paragraph(para_text, body_style)
                
                # Alternate pastel backgrounds
                bg_color = PASTEL_COLORS[color_list[(idx + sent_idx) % len(color_list)]]
                
                content_table = Table(
                    [[para]], 
                    colWidths=[content_width - 40]
                )
                content_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), bg_color),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
                    ('ROUNDEDCORNERS', [5, 5, 5, 5]),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ]))
                flowables.append(content_table)
                flowables.append(Spacer(1, 8))

    # ========== DECORATIVE FOOTER ==========
    flowables.append(Spacer(1, 20))
    
    # Encouraging footer with emojis
    footer_messages = [
        "🎉 Bravo ! Continue à apprendre et à grandir ! 🎉",
        "🌟 Tu es un super apprenant ! Continue comme ça ! 🌟",
        "💪 Excellent travail ! Tu progresses chaque jour ! 💪",
        "🏆 Félicitations pour ton apprentissage ! �"
    ]
    import random
    footer_text = random.choice(footer_messages)
    footer_para = Paragraph(footer_text, footer_style)
    
    footer_table = Table(
        [[footer_para]], 
        colWidths=[content_width]
    )
    footer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PASTEL_COLORS['yellow']),
        ('BOX', (0, 0), (-1, -1), 1.5, ACCENT_COLORS['yellow']),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    flowables.append(footer_table)
    
    # Add small EduKids branding
    flowables.append(Spacer(1, 10))
    brand_style = ParagraphStyle(
        'Brand',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.HexColor('#95A5A6'),
    )
    flowables.append(Paragraph("📚 EduKids - Apprendre en s'amusant 📚", brand_style))

    # Build the PDF
    doc.build(flowables)
    return buffer.getvalue()
