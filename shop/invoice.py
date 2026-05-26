import io
import os
from decimal import Decimal
from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Nazwy fontów (zarejestrowane w _register_fonts) ─────
FONT_NORMAL = 'Arial'
FONT_BOLD = 'Arial-Bold'

# ── Kolory ──────────────────────────────────────────────
COLOR_PRIMARY = colors.HexColor('#1a1a2e')
COLOR_ACCENT = colors.HexColor('#6c5ce7')
COLOR_ACCENT_LIGHT = colors.HexColor('#f0edff')
COLOR_GRAY = colors.HexColor('#666666')
COLOR_LIGHT_GRAY = colors.HexColor('#f5f5f5')
COLOR_BORDER = colors.HexColor('#e0e0e0')
COLOR_WHITE = colors.white

# ── Dane sprzedawcy (placeholder) ───────────────────────
SELLER_NAME = 'Sklep Django Sp. z o.o.'
SELLER_ADDRESS = 'ul. Przykładowa 1'
SELLER_CITY = '00-001 Warszawa'
SELLER_NIP = 'NIP: 1234567890'
SELLER_EMAIL = 'kontakt@sklep.pl'


_fonts_registered = False


def _register_fonts():
    """Register TTF fonts with full Polish character support."""
    global _fonts_registered
    if _fonts_registered:
        return

    # Windows: use Arial from system fonts
    fonts_dir = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')
    arial_path = os.path.join(fonts_dir, 'arial.ttf')
    arial_bold_path = os.path.join(fonts_dir, 'arialbd.ttf')

    if os.path.exists(arial_path):
        pdfmetrics.registerFont(TTFont(FONT_NORMAL, arial_path))
    if os.path.exists(arial_bold_path):
        pdfmetrics.registerFont(TTFont(FONT_BOLD, arial_bold_path))

    _fonts_registered = True


def _get_styles():
    """Create custom paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Title'],
        fontSize=28,
        textColor=COLOR_PRIMARY,
        spaceAfter=2 * mm,
        alignment=TA_LEFT,
        fontName=FONT_BOLD,
    ))

    styles.add(ParagraphStyle(
        'InvoiceNumber',
        parent=styles['Normal'],
        fontSize=11,
        textColor=COLOR_ACCENT,
        fontName=FONT_BOLD,
    ))

    styles.add(ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor=COLOR_ACCENT,
        fontName=FONT_BOLD,
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    ))

    styles.add(ParagraphStyle(
        'InfoText',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_PRIMARY,
        fontName=FONT_NORMAL,
        leading=14,
    ))

    styles.add(ParagraphStyle(
        'InfoTextGray',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_GRAY,
        fontName=FONT_NORMAL,
        leading=14,
    ))

    styles.add(ParagraphStyle(
        'FooterText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=COLOR_GRAY,
        fontName=FONT_NORMAL,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=8,
        textColor=COLOR_WHITE,
        fontName=FONT_BOLD,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_PRIMARY,
        fontName=FONT_NORMAL,
    ))

    styles.add(ParagraphStyle(
        'TableCellRight',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_PRIMARY,
        fontName=FONT_NORMAL,
        alignment=TA_RIGHT,
    ))

    styles.add(ParagraphStyle(
        'TableCellCenter',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_PRIMARY,
        fontName=FONT_NORMAL,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        'TotalLabel',
        parent=styles['Normal'],
        fontSize=11,
        textColor=COLOR_PRIMARY,
        fontName=FONT_BOLD,
        alignment=TA_RIGHT,
    ))

    styles.add(ParagraphStyle(
        'TotalValue',
        parent=styles['Normal'],
        fontSize=14,
        textColor=COLOR_ACCENT,
        fontName=FONT_BOLD,
        alignment=TA_RIGHT,
    ))

    return styles


def _safe(text):
    """Make text safe for ReportLab Paragraphs (escape XML entities)."""
    if text is None:
        return ''
    text = str(text)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def generate_invoice_pdf(order):
    """
    Generate a PDF invoice for given Order and return HttpResponse.
    """
    _register_fonts()
    styles = _get_styles()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
    )

    elements = []
    now = timezone.now()
    invoice_number = f'FV/{order.id}/{order.created_at.year}'

    # ── Nagłówek: FAKTURA + numer ────────────────────────
    elements.append(Paragraph('FAKTURA', styles['InvoiceTitle']))
    elements.append(Paragraph(f'Nr {_safe(invoice_number)}', styles['InvoiceNumber']))
    elements.append(Spacer(1, 3 * mm))

    # Linia dekoracyjna
    elements.append(HRFlowable(
        width='100%', thickness=2, color=COLOR_ACCENT,
        spaceAfter=5 * mm, spaceBefore=2 * mm
    ))

    # ── Daty + metoda płatności ───────────────────────────
    date_data = [
        [
            Paragraph('Data zamówienia:', styles['InfoTextGray']),
            Paragraph(_safe(order.created_at.strftime('%d.%m.%Y, %H:%M')), styles['InfoText']),
            Paragraph('Data wystawienia:', styles['InfoTextGray']),
            Paragraph(_safe(now.strftime('%d.%m.%Y')), styles['InfoText']),
        ],
        [
            Paragraph('Metoda płatności:', styles['InfoTextGray']),
            Paragraph(_safe(order.payment_method_display), styles['InfoText']),
            Paragraph('Status:', styles['InfoTextGray']),
            Paragraph(_safe(order.get_status_display()), styles['InfoText']),
        ],
    ]

    date_table = Table(date_data, colWidths=[35 * mm, 45 * mm, 35 * mm, 45 * mm])
    date_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(date_table)
    elements.append(Spacer(1, 5 * mm))

    # ── Sprzedawca / Nabywca ─────────────────────────────
    seller_lines = [
        Paragraph('SPRZEDAWCA', styles['SectionHeader']),
        Paragraph(_safe(SELLER_NAME), styles['InfoText']),
        Paragraph(_safe(SELLER_ADDRESS), styles['InfoText']),
        Paragraph(_safe(SELLER_CITY), styles['InfoText']),
        Paragraph(_safe(SELLER_NIP), styles['InfoText']),
        Paragraph(_safe(SELLER_EMAIL), styles['InfoTextGray']),
    ]

    # Buduj dane nabywcy
    buyer_name = order.customer_name or '—'
    buyer_email = order.customer_email or ''
    buyer_phone = order.customer_phone or ''
    buyer_address = order.shipping_address or ''

    buyer_lines = [
        Paragraph('NABYWCA', styles['SectionHeader']),
        Paragraph(_safe(buyer_name), styles['InfoText']),
    ]
    if buyer_address:
        buyer_lines.append(Paragraph(_safe(buyer_address), styles['InfoText']))
    if buyer_email:
        buyer_lines.append(Paragraph(_safe(buyer_email), styles['InfoTextGray']))
    if buyer_phone:
        buyer_lines.append(Paragraph(f'Tel: {_safe(buyer_phone)}', styles['InfoTextGray']))

    # Pad to same length for table alignment
    max_len = max(len(seller_lines), len(buyer_lines))
    while len(seller_lines) < max_len:
        seller_lines.append(Paragraph('', styles['InfoText']))
    while len(buyer_lines) < max_len:
        buyer_lines.append(Paragraph('', styles['InfoText']))

    parties_data = list(zip(seller_lines, buyer_lines))
    parties_table = Table(parties_data, colWidths=[85 * mm, 85 * mm])
    parties_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(parties_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Tabela produktów ─────────────────────────────────
    elements.append(Paragraph('POZYCJE', styles['SectionHeader']))

    # Nagłówki tabeli
    header_row = [
        Paragraph('Lp.', styles['TableHeader']),
        Paragraph('Nazwa produktu', styles['TableHeader']),
        Paragraph('Ilość', styles['TableHeader']),
        Paragraph('Cena jedn.', styles['TableHeader']),
        Paragraph('Wartość', styles['TableHeader']),
    ]

    table_data = [header_row]
    items = order.items.all()

    for idx, item in enumerate(items, 1):
        item_total = item.price * item.quantity
        row = [
            Paragraph(str(idx), styles['TableCellCenter']),
            Paragraph(_safe(item.get_display_name()), styles['TableCell']),
            Paragraph(str(item.quantity), styles['TableCellCenter']),
            Paragraph(f'{item.price:.2f} zł', styles['TableCellRight']),
            Paragraph(f'{item_total:.2f} zł', styles['TableCellRight']),
        ]
        table_data.append(row)

    col_widths = [12 * mm, 75 * mm, 18 * mm, 30 * mm, 30 * mm]
    product_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Style tabeli
    table_style_commands = [
        # Nagłówek
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_WHITE),
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),

        # Wiersze danych
        ('FONTNAME', (0, 1), (-1, -1), FONT_NORMAL),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),

        # Siatka
        ('LINEBELOW', (0, 0), (-1, 0), 1, COLOR_ACCENT),
        ('LINEBELOW', (0, -1), (-1, -1), 1, COLOR_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Wyrównanie kolumn
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Lp.
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),  # Ilość
        ('ALIGN', (3, 0), (4, -1), 'RIGHT'),   # Ceny
    ]

    # Alternatywne tło wierszy (zebra)
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            table_style_commands.append(
                ('BACKGROUND', (0, i), (-1, i), COLOR_LIGHT_GRAY)
            )
        # Dolna linia każdego wiersza
        table_style_commands.append(
            ('LINEBELOW', (0, i), (-1, i), 0.5, COLOR_BORDER)
        )

    product_table.setStyle(TableStyle(table_style_commands))
    elements.append(product_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Podsumowanie ─────────────────────────────────────
    summary_data = []

    # Suma produktów (przed rabatem)
    original_total = order.original_total or order.total_price
    summary_data.append([
        Paragraph('Suma produktów:', styles['InfoText']),
        Paragraph(f'{original_total:.2f} zł', styles['InfoText']),
    ])

    # Rabat
    if order.discount_amount and order.discount_amount > 0:
        discount_label = 'Rabat'
        if order.discount_code:
            discount_label += f' ({_safe(order.discount_code.code)})'
        discount_label += ':'
        summary_data.append([
            Paragraph(discount_label, styles['InfoText']),
            Paragraph(f'-{order.discount_amount:.2f} zł', styles['InfoText']),
        ])

    # Dostawa
    if order.shipping_cost and order.shipping_cost > 0:
        shipping_label = 'Dostawa'
        if order.shipping_method_name:
            shipping_label += f' ({_safe(order.shipping_method_name)})'
        shipping_label += ':'
        summary_data.append([
            Paragraph(shipping_label, styles['InfoText']),
            Paragraph(f'{order.shipping_cost:.2f} zł', styles['InfoText']),
        ])

    # RAZEM
    summary_data.append([
        Paragraph('<b>RAZEM DO ZAPŁATY:</b>', styles['TotalLabel']),
        Paragraph(f'<b>{order.total_price:.2f} zł</b>', styles['TotalValue']),
    ])

    summary_table = Table(
        summary_data,
        colWidths=[120 * mm, 45 * mm],
        hAlign='RIGHT',
    )
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        # Linia nad RAZEM
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, COLOR_ACCENT),
        ('TOPPADDING', (0, -1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 15 * mm))

    # ── Stopka ───────────────────────────────────────────
    elements.append(HRFlowable(
        width='100%', thickness=0.5, color=COLOR_BORDER,
        spaceAfter=3 * mm, spaceBefore=3 * mm
    ))
    elements.append(Paragraph(
        'Dokument wygenerowany automatycznie — nie wymaga podpisu.',
        styles['FooterText']
    ))
    elements.append(Paragraph(
        f'Sklep Django • {now.strftime("%d.%m.%Y %H:%M")}',
        styles['FooterText']
    ))

    # ── Buduj PDF ────────────────────────────────────────
    doc.build(elements)
    buffer.seek(0)

    filename = f'faktura_{invoice_number.replace("/", "_")}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
