import json, urllib.request, urllib.parse, re, os
from html.parser import HTMLParser
from datetime import date

# ─────────────────────────────────────────────────────────────
# CONFIG — pas aan per protocol dat je toevoegt
# ─────────────────────────────────────────────────────────────
# protocollen-config.json bevat de Google Docs IDs per protocol.
# Structuur:
# {
#   "protocollen": [
#     {
#       "id": "motorische-ontwikkelingsachterstand",
#       "naam": "Motorische ontwikkelingsachterstand",
#       "zone": "motoriek",
#       "niveaus": {
#         "makkelijk": "GOOGLE_DOC_ID_HIER",
#         "gemiddeld": "GOOGLE_DOC_ID_HIER",
#         "complex":   "GOOGLE_DOC_ID_HIER"
#       }
#     }
#   ]
# }
#
# Zone-waarden (gebruik exact deze strings):
#   motoriek · schrijven · sport · houding · ademhaling
#   zuigeling · sensorisch · revalidatie · complexe-ontwikkeling · manueel

with open('protocollen-config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# ─────────────────────────────────────────────────────────────
# ZONES
# ─────────────────────────────────────────────────────────────
ZONES = {
    'motoriek':              'Motorische ontwikkeling',
    'schrijven':             'Schrijven & fijne motoriek',
    'sport':                 'Sport, groei & blessures',
    'houding':               'Houding & wervelkolom',
    'ademhaling':            'Ademhaling',
    'zuigeling':             'Zuigeling & jong kind',
    'sensorisch':            'Sensorische prikkelverwerking',
    'revalidatie':           'Revalidatie & operatie',
    'complexe-ontwikkeling': 'Complexe ontwikkeling',
    'manueel':               'Manuele therapie bij kinderen',
}

ZONE_ICONS = {
    'motoriek':              '🏃',
    'schrijven':             '✏️',
    'sport':                 '⚽',
    'houding':               '🦴',
    'ademhaling':            '💨',
    'zuigeling':             '👶',
    'sensorisch':            '🎯',
    'revalidatie':           '🏥',
    'complexe-ontwikkeling': '🧩',
    'manueel':               '🙌',
}

SITE_URL   = 'https://kansrijkopgroeien.net'
SITE_NAAM  = 'Kansrijk Opgroeien'
LOGO_BESTAND = 'Kansrijkopgroeien_logo.png'
KLEUR_PRIMARY = '#E8735A'   # oranje
KLEUR_LIGHT   = '#FDF0ED'
KLEUR_NAVY    = '#2C3E50'
KLEUR_TEAL    = '#4CAF50'   # groen accent

# ─────────────────────────────────────────────────────────────
# HTML VERWERKING
# ─────────────────────────────────────────────────────────────
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False
    def handle_starttag(self, tag, attrs):
        if tag in ('style', 'script'):
            self.skip = True
    def handle_endtag(self, tag):
        if tag in ('style', 'script'):
            self.skip = False
        if tag in ('p', 'li', 'h1', 'h2', 'h3', 'br', 'tr'):
            self.text.append(' ')
    def handle_data(self, data):
        if not self.skip:
            self.text.append(data)
    def get_text(self):
        return ' '.join(' '.join(self.text).split())

def opschonen_html(body):
    body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
    body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
    body = re.sub(r'<img[^>]*/?>', '', body)
    body = re.sub(r'<figure[^>]*>.*?</figure>', '', body, flags=re.DOTALL)

    # Ontgoogle links
    def ontgoogle(match):
        href = match.group(1)
        if 'google.com/url' in href:
            href = href.replace('&amp;', '&')
            parsed = urllib.parse.urlparse(href)
            params = urllib.parse.parse_qs(parsed.query)
            echte_url = params.get('q', [href])[0]
            return f'href="{echte_url}"'
        return match.group(0)
    body = re.sub(r'href="([^"]*)"', ontgoogle, body)

    body = re.sub(r' style="[^"]*"', '', body)
    body = re.sub(r' class="[^"]*"', '', body)
    body = re.sub(r' id="[^"]*"', '', body)
    body = re.sub(r'<hr[^>]*>', '<hr>', body)
    body = re.sub(r'\n{3,}', '\n\n', body)

    # Fysioefeningen-links omzetten naar knoppen
    def maak_knop_van_link(match):
        url = match.group(1)
        linktekst = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        naam = linktekst if linktekst and not linktekst.startswith('http') else \
               url.split('/')[-1].replace('-', ' ').strip().capitalize()
        return (
            f'<a href="{url}" target="_blank" rel="noopener" '
            f'style="display:inline-flex;align-items:center;gap:8px;margin:6px 0;padding:10px 18px;'
            f'background:{KLEUR_LIGHT};color:{KLEUR_PRIMARY};border:2px solid {KLEUR_PRIMARY};border-radius:8px;'
            f'font-size:0.875rem;font-weight:600;text-decoration:none;">&#128249; {naam}</a>'
        )
    body = re.sub(
        r'<a href="(https?://(?:www\.)?fysioefeningen\.nl/[^"]+)"[^>]*>(.*?)</a>',
        maak_knop_van_link, body, flags=re.DOTALL
    )

    # [VIDEO: naam | url] shortcodes
    def maak_video_knop(match):
        naam = match.group(1).strip()
        url  = match.group(2).strip()
        return (
            f'<a href="{url}" target="_blank" rel="noopener" '
            f'style="display:inline-flex;align-items:center;gap:6px;margin:4px 0;padding:6px 14px;'
            f'background:{KLEUR_LIGHT};color:{KLEUR_PRIMARY};border:1.5px solid {KLEUR_PRIMARY};border-radius:6px;'
            f'font-size:0.8rem;font-weight:600;text-decoration:none;">📹 {naam}</a>'
        )
    body = re.sub(r'\[VIDEO:\s*([^|\]]+)\|\s*(https?://[^\]]+)\]', maak_video_knop, body)

    body = re.sub(r'<span>\s*</span>', '', body)
    body = re.sub(r'<span>(.*?)</span>', r'\1', body)
    body = re.sub(r'<p>\s*</p>', '', body)
    body = re.sub(r'<div>\s*</div>', '', body)

    return body.strip()

def extraheer_preview(body, max_alineas=3):
    body = opschonen_html(body)
    blokken = re.findall(r'<(p|h1|h2|h3)[^>]*>.*?</\1>', body, re.DOTALL | re.IGNORECASE)
    blokken = [b for b in blokken if len(re.sub(r'<[^>]+>', '', b).strip()) > 10]
    return '\n'.join(blokken[:max_alineas])

# ─────────────────────────────────────────────────────────────
# VOLLEDIGE HTML PAGINA PER PROTOCOL
# ─────────────────────────────────────────────────────────────
def maak_niveau_label(niveau):
    return {'makkelijk': '📗 Makkelijk', 'gemiddeld': '📘 Gemiddeld', 'complex': '📕 Complex'}.get(niveau, niveau.capitalize())

def maak_cta_blok():
    return f'''
<div style="margin-top:3rem;border-top:2px solid {KLEUR_LIGHT};padding-top:2rem;">
  <div style="background:{KLEUR_NAVY};border-radius:14px;padding:2rem;">
    <h2 style="font-size:1.1rem;font-weight:700;color:white;margin-bottom:0.5rem;">Klaar om aan de slag te gaan?</h2>
    <p style="font-size:0.88rem;color:rgba(255,255,255,0.7);margin-bottom:1.5rem;">Vind een gespecialiseerde kinderfysiotherapeut bij u in de buurt.</p>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <a href="../index.html#zoeken" style="background:{KLEUR_PRIMARY};color:white;padding:11px 22px;border-radius:8px;font-size:0.9rem;font-weight:700;text-decoration:none;">🗺 Vind een therapeut bij mij in de buurt</a>
      <a href="../therapeut-aanmelden.html" style="background:transparent;color:rgba(255,255,255,0.8);border:1.5px solid rgba(255,255,255,0.3);padding:11px 22px;border-radius:8px;font-size:0.9rem;font-weight:600;text-decoration:none;">Aanmelden als therapeut</a>
    </div>
  </div>
</div>'''

def maak_html_pagina(protocol_naam, protocol_id, niveau, body_schoon, zone_id):
    zone_naam   = ZONES.get(zone_id, zone_id.capitalize())
    zone_icon   = ZONE_ICONS.get(zone_id, '🏥')
    niveau_label = maak_niveau_label(niveau)

    andere_niveaus = [n for n in ['makkelijk', 'gemiddeld', 'complex'] if n != niveau]
    andere_niveaus_html = ''.join(
        f'<a href="{protocol_id}-{n}.html" style="padding:6px 14px;border-radius:6px;font-size:0.78rem;font-weight:600;background:var(--grey-bg);color:var(--text-muted);border:1px solid var(--grey-border);text-decoration:none;">{maak_niveau_label(n)}</a>\n'
        for n in andere_niveaus
    )

    extractor = TextExtractor()
    extractor.feed(body_schoon)
    tekst_preview = extractor.get_text()[:200].strip()
    description = f"Behandelprotocol {protocol_naam.lower()} voor kinderfysiotherapeuten. {tekst_preview}..."

    return f'''<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{protocol_naam} – {niveau_label} | {SITE_NAAM}</title>
  <meta name="description" content="{description}" />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="{SITE_URL}/protocollen/{protocol_id}-{niveau}.html" />
  <meta property="og:title" content="{protocol_naam} | {SITE_NAAM}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:type" content="article" />
  <style>
    @font-face {{ font-family: 'Inter'; src: url('../fonts/inter-v20-latin-300.woff2') format('woff2'); font-weight: 300; font-display: swap; }}
    @font-face {{ font-family: 'Inter'; src: url('../fonts/inter-v20-latin-regular.woff2') format('woff2'); font-weight: 400; font-display: swap; }}
    @font-face {{ font-family: 'Inter'; src: url('../fonts/inter-v20-latin-500.woff2') format('woff2'); font-weight: 500; font-display: swap; }}
    @font-face {{ font-family: 'Inter'; src: url('../fonts/inter-v20-latin-600.woff2') format('woff2'); font-weight: 600; font-display: swap; }}
    @font-face {{ font-family: 'Inter'; src: url('../fonts/inter-v20-latin-700.woff2') format('woff2'); font-weight: 700; font-display: swap; }}
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --oranje: {KLEUR_PRIMARY}; --oranje-light: {KLEUR_LIGHT};
      --navy: {KLEUR_NAVY}; --grey-bg: #F8F9FA; --grey-border: #E8ECF0;
      --text: {KLEUR_NAVY}; --text-muted: #7F8C8D; --white: #FFFFFF;
    }}
    html {{ scroll-behavior: smooth; }}
    body {{ font-family: 'Inter', sans-serif; font-size: 16px; color: var(--text); background: var(--grey-bg); line-height: 1.6; }}
    header {{ background: var(--white); border-bottom: 1px solid var(--grey-border); position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }}
    .header-inner {{ max-width: 1100px; margin: 0 auto; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; height: 72px; }}
    .logo {{ display: flex; align-items: center; gap: 12px; text-decoration: none; }}
    .logo img {{ height: 48px; width: 48px; object-fit: contain; }}
    .logo-text {{ font-weight: 700; font-size: 1rem; color: var(--navy); }}
    .logo-text span {{ color: var(--oranje); }}
    nav {{ display: flex; gap: 4px; }}
    nav a {{ color: var(--text-muted); text-decoration: none; font-size: 0.85rem; font-weight: 500; padding: 7px 12px; border-radius: 8px; transition: all 0.2s; }}
    nav a:hover {{ background: var(--grey-bg); color: var(--navy); }}
    nav a.cta {{ background: var(--oranje); color: var(--white); font-weight: 700; }}
    @media (max-width: 700px) {{ nav {{ display: none; }} }}
    .breadcrumb {{ max-width: 860px; margin: 24px auto 0; padding: 0 24px; font-size: 0.82rem; color: var(--text-muted); }}
    .breadcrumb a {{ color: var(--oranje); text-decoration: none; }}
    .page-header {{ max-width: 860px; margin: 16px auto 0; padding: 0 24px; }}
    .zone-badge {{ display: inline-flex; align-items: center; gap: 6px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--oranje); background: var(--oranje-light); padding: 3px 12px; border-radius: 999px; margin-bottom: 10px; }}
    h1 {{ font-size: clamp(1.5rem, 3vw, 2rem); font-weight: 700; color: var(--navy); line-height: 1.25; margin-bottom: 12px; }}
    .niveau-badges {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px; }}
    .niveau-actief {{ padding: 6px 14px; border-radius: 6px; font-size: 0.78rem; font-weight: 700; background: var(--navy); color: white; }}
    .content-wrap {{ max-width: 860px; margin: 0 auto 64px; padding: 0 24px; }}
    .disclaimer {{ background: #FEF9E7; border: 1px solid #F0D060; border-radius: 8px; padding: 12px 16px; font-size: 0.82rem; color: #7D6608; margin-bottom: 24px; }}
    .terug-link {{ display: inline-flex; align-items: center; gap: 6px; color: var(--oranje); font-size: 0.85rem; font-weight: 600; text-decoration: none; margin-bottom: 20px; }}
    .content {{ background: var(--white); border: 1px solid var(--grey-border); border-radius: 14px; padding: clamp(1.5rem, 4vw, 3rem); font-size: 0.92rem; line-height: 1.8; }}
    .content h2 {{ font-size: 1.15rem; font-weight: 700; color: var(--navy); margin: 1.6em 0 0.5em; padding-bottom: 6px; border-bottom: 2px solid var(--oranje-light); }}
    .content h3 {{ font-size: 1rem; font-weight: 700; color: var(--navy); margin: 1.2em 0 0.4em; }}
    .content h4 {{ font-size: 0.9rem; font-weight: 700; color: var(--text-muted); margin: 1em 0 0.3em; text-transform: uppercase; letter-spacing: 0.05em; }}
    .content p {{ margin-bottom: 0.9em; }}
    .content ul, .content ol {{ margin: 0.4em 0 0.9em 1.6em; }}
    .content li {{ margin-bottom: 0.35em; }}
    .content hr {{ border: none; border-top: 1px solid var(--grey-border); margin: 1.8em 0; }}
    .content table {{ width: 100%; border-collapse: collapse; margin: 1em 0; font-size: 0.85rem; }}
    .content td, .content th {{ border: 1px solid var(--grey-border); padding: 8px 12px; text-align: left; }}
    .content th {{ background: var(--grey-bg); font-weight: 600; }}
    footer {{ background: {KLEUR_NAVY}; color: rgba(255,255,255,0.4); text-align: center; padding: 28px 24px; font-size: 0.82rem; margin-top: 48px; }}
    footer a {{ color: rgba(255,255,255,0.6); text-decoration: none; }}
  </style>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "MedicalWebPage",
    "name": "{protocol_naam} – {SITE_NAAM}",
    "description": "{description}",
    "url": "{SITE_URL}/protocollen/{protocol_id}-{niveau}.html",
    "inLanguage": "nl",
    "isPartOf": {{"@type": "WebSite", "name": "{SITE_NAAM}", "url": "{SITE_URL}"}},
    "about": {{"@type": "MedicalCondition", "name": "{protocol_naam}"}}
  }}
  </script>
</head>
<body>

<header>
  <div class="header-inner">
    <a href="../index.html" class="logo">
      <img src="../{LOGO_BESTAND}" alt="{SITE_NAAM}" />
      <div class="logo-text"><span>Kansrijk</span> Opgroeien</div>
    </a>
    <nav>
      <a href="../protocollen.html">Protocollen</a>
      <a href="../index.html#zoeken">Zoeken</a>
      <a href="../index.html#specialisaties">Specialisaties</a>
      <a href="../therapeut-aanmelden.html" class="cta">Aanmelden</a>
    </nav>
  </div>
</header>

<div class="breadcrumb">
  <a href="../index.html">Home</a> &rsaquo;
  <a href="../protocollen.html">Protocollen</a> &rsaquo;
  {protocol_naam}
</div>

<div class="page-header">
  <div class="zone-badge">{zone_icon} {zone_naam}</div>
  <h1>{protocol_naam}</h1>
  <div class="niveau-badges">
    <span class="niveau-actief">{niveau_label}</span>
    {andere_niveaus_html}
  </div>
</div>

<div class="content-wrap">
  <div class="disclaimer">
    ⚠️ Dit protocol is algemene informatie voor zorgverleners en ouders. Het vervangt geen persoonlijk advies van een arts of kinderfysiotherapeut.
  </div>
  <a href="../protocollen.html" class="terug-link">&#8592; Terug naar alle protocollen</a>
  <div class="content">
    {body_schoon}
  </div>
  {maak_cta_blok()}
</div>

<footer>
  <p>&copy; 2025 {SITE_NAAM} &nbsp;&middot;&nbsp; <a href="../index.html">Home</a> &nbsp;&middot;&nbsp; <a href="../protocollen.html">Protocollen</a> &nbsp;&middot;&nbsp; <a href="https://vindjefysio.net">VindJeFysio Netwerk</a></p>
</footer>
</body>
</html>'''

# ─────────────────────────────────────────────────────────────
# HOOFDLOOP — protocollen ophalen en genereren
# ─────────────────────────────────────────────────────────────
os.makedirs('protocollen', exist_ok=True)
fouten = []
protocol_data = []

for protocol in config['protocollen']:
    protocol_teksten      = {}
    protocol_previews     = {}
    protocol_volledige_html = {}
    protocol_ruwe_html    = {}

    for niveau, doc_id in protocol['niveaus'].items():
        if not doc_id or doc_id in ('INVULLEN', ''):
            print(f"Overgeslagen: {protocol['id']} – {niveau} (geen doc_id)")
            continue

        url = f"https://docs.google.com/document/d/{doc_id}/export?format=html"
        bestandsnaam = f"protocollen/{protocol['id']}-{niveau}.html"

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode('utf-8')

            body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
            if body_match:
                body       = body_match.group(1)
                body_schoon = opschonen_html(body)

                volledige_pagina = maak_html_pagina(
                    protocol_naam=protocol['naam'],
                    protocol_id=protocol['id'],
                    niveau=niveau,
                    body_schoon=body_schoon,
                    zone_id=protocol.get('zone', '')
                )
                with open(bestandsnaam, 'w', encoding='utf-8') as out:
                    out.write(volledige_pagina)

                print(f"✓ {bestandsnaam}")

                extractor = TextExtractor()
                extractor.feed(body_schoon)
                protocol_teksten[niveau]       = extractor.get_text()[:2000]
                protocol_previews[niveau]      = extraheer_preview(body, max_alineas=3)
                protocol_volledige_html[niveau] = body_schoon
                protocol_ruwe_html[niveau]     = body
            else:
                fouten.append(bestandsnaam)
                print(f"✗ Geen body gevonden: {bestandsnaam}")

        except Exception as e:
            fouten.append(f"{bestandsnaam}: {e}")
            print(f"✗ Fout: {bestandsnaam}: {e}")

    if protocol_teksten:
        protocol_data.append({
            'id':             protocol['id'],
            'naam':           protocol['naam'],
            'zone':           protocol.get('zone', ''),
            'teksten':        protocol_teksten,
            'previews':       protocol_previews,
            'volledige_html': protocol_volledige_html,
            'ruwe_html':      protocol_ruwe_html,
        })

# ─────────────────────────────────────────────────────────────
# GENEREER protocollen.html
# ─────────────────────────────────────────────────────────────
print("\nGenereer protocollen.html...")

NIVEAU_EMOJIS  = {'makkelijk': '📗', 'gemiddeld': '📘', 'complex': '📕'}
NIVEAU_LABELS  = {'makkelijk': 'Makkelijk', 'gemiddeld': 'Gemiddeld', 'complex': 'Complex'}

protocol_kaarten = ''
for p in protocol_data:
    zone_id   = p['zone']
    zone_naam = ZONES.get(zone_id, zone_id.capitalize())
    zone_icon = ZONE_ICONS.get(zone_id, '🏥')

    preview_html = p['previews'].get('makkelijk', p['previews'].get('gemiddeld', '<p>Geen preview beschikbaar.</p>'))
    tekst_data   = p['teksten'].get('makkelijk', p['teksten'].get('gemiddeld', ''))
    tekst_data   = tekst_data[:500].lower().replace('"', '').replace("'", '')

    import json as jsonlib
    volledige_json = jsonlib.dumps(p['volledige_html'])

    niveaus_html = ''
    for n in p['teksten'].keys():
        emoji = NIVEAU_EMOJIS.get(n, '')
        label = NIVEAU_LABELS.get(n, n.capitalize())
        niveaus_html += f'<button class="niveau-btn niveau-{n}" onclick="openProtocol(\'{p["id"]}\', \'{n}\')">{emoji} {label}</button>\n'

    protocol_kaarten += f'''<div class="protocol-kaart" id="kaart-{p['id']}" data-naam="{p['naam'].lower()}" data-zone="{zone_id}" data-tekst="{tekst_data}" data-html="{volledige_json.replace('"', '&quot;')}">
  <div class="zone-badge"><span>{zone_icon}</span>{zone_naam}</div>
  <h2 class="protocol-naam">{p['naam']}</h2>
  <div class="protocol-preview">{preview_html}</div>
  <div class="protocol-niveaus">
    {niveaus_html}
  </div>
  <div class="protocol-viewer" id="viewer-{p['id']}" style="display:none">
    <div class="viewer-header">
      <span id="viewer-titel-{p['id']}"></span>
      <button onclick="sluitProtocol('{p['id']}')" style="background:none;border:none;cursor:pointer;font-size:1.2rem;color:#7F8C8D">✕</button>
    </div>
    <div class="viewer-inhoud" id="viewer-inhoud-{p['id']}"></div>
  </div>
</div>'''

zone_filter_btns = '<button class="zone-btn actief" onclick="filterZone(this, \'alle\')">Alle specialisaties</button>\n'
for zone_id, zone_naam in ZONES.items():
    icon = ZONE_ICONS.get(zone_id, '')
    zone_filter_btns += f'<button class="zone-btn" onclick="filterZone(this, \'{zone_id}\')">{icon} {zone_naam}</button>\n'

protocollen_html = f'''<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Behandelprotocollen kinderfysiotherapie – {SITE_NAAM}</title>
  <meta name="description" content="Overzicht van behandelprotocollen voor kinderfysiotherapeuten. Motorische ontwikkeling, DCD, schrijfproblemen, houding, ademhaling en meer." />
  <style>
    @font-face {{ font-family: 'Inter'; src: url('fonts/inter-v20-latin-300.woff2') format('woff2'); font-weight: 300; font-display: swap; }}
    @font-face {{ font-family: 'Inter'; src: url('fonts/inter-v20-latin-regular.woff2') format('woff2'); font-weight: 400; font-display: swap; }}
    @font-face {{ font-family: 'Inter'; src: url('fonts/inter-v20-latin-500.woff2') format('woff2'); font-weight: 500; font-display: swap; }}
    @font-face {{ font-family: 'Inter'; src: url('fonts/inter-v20-latin-600.woff2') format('woff2'); font-weight: 600; font-display: swap; }}
    @font-face {{ font-family: 'Inter'; src: url('fonts/inter-v20-latin-700.woff2') format('woff2'); font-weight: 700; font-display: swap; }}
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --oranje: {KLEUR_PRIMARY}; --oranje-light: {KLEUR_LIGHT};
      --navy: {KLEUR_NAVY}; --grey-bg: #F8F9FA; --grey-border: #E8ECF0;
      --text: {KLEUR_NAVY}; --text-muted: #7F8C8D; --white: #FFFFFF;
    }}
    html {{ scroll-behavior: smooth; }}
    body {{ font-family: 'Inter', sans-serif; font-size: 16px; color: var(--text); background: var(--grey-bg); line-height: 1.6; }}

    header {{ background: var(--white); border-bottom: 1px solid var(--grey-border); position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }}
    .header-inner {{ max-width: 1100px; margin: 0 auto; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; height: 72px; }}
    .logo {{ display: flex; align-items: center; gap: 12px; text-decoration: none; }}
    .logo img {{ height: 48px; width: 48px; object-fit: contain; }}
    .logo-text {{ font-weight: 700; font-size: 1rem; color: var(--navy); }}
    .logo-text span {{ color: var(--oranje); }}
    nav {{ display: flex; gap: 4px; }}
    nav a {{ color: var(--text-muted); text-decoration: none; font-size: 0.85rem; font-weight: 500; padding: 7px 12px; border-radius: 8px; transition: all 0.2s; }}
    nav a:hover {{ background: var(--grey-bg); color: var(--navy); }}
    nav a.cta {{ background: var(--oranje); color: var(--white); font-weight: 700; }}
    @media (max-width: 700px) {{ nav {{ display: none; }} }}

    .hero {{ background: linear-gradient(135deg, #E8735A 0%, #F5A623 50%, #4CAF50 100%); color: white; padding: 56px 24px 48px; text-align: center; position: relative; overflow: hidden; }}
    .hero::before {{ content:''; position:absolute; inset:0; background:rgba(0,0,0,0.3); }}
    .hero-content {{ position: relative; z-index: 1; }}
    .hero h1 {{ font-size: clamp(1.8rem, 4vw, 2.4rem); font-weight: 700; margin-bottom: 12px; letter-spacing: -0.02em; text-shadow: 0 2px 8px rgba(0,0,0,0.2); }}
    .hero h1 em {{ font-style: normal; color: #FFE082; }}
    .hero p {{ opacity: 0.9; max-width: 560px; margin: 0 auto 28px; font-size: 0.95rem; }}
    .zoekbalk-wrap {{ max-width: 560px; margin: 0 auto; }}
    .zoekbalk {{ display: flex; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }}
    .zoekbalk input {{ flex: 1; padding: 14px 20px; border: none; outline: none; font-family: inherit; font-size: 1rem; color: var(--text); }}
    .zoekbalk button {{ padding: 14px 24px; background: var(--oranje); color: white; border: none; cursor: pointer; font-weight: 700; font-size: 0.9rem; transition: background 0.2s; }}
    .zoekbalk button:hover {{ background: #d4614a; }}

    .filter-wrap {{ max-width: 1100px; margin: 32px auto 0; padding: 0 24px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
    .filter-label {{ font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-right: 4px; white-space: nowrap; }}
    .zone-btn {{ padding: 6px 14px; border-radius: 999px; border: 1.5px solid var(--grey-border); background: var(--white); color: var(--text-muted); font-size: 0.8rem; font-weight: 600; cursor: pointer; transition: all 0.2s; font-family: inherit; }}
    .zone-btn:hover, .zone-btn.actief {{ background: var(--oranje); border-color: var(--oranje); color: white; }}

    .container {{ max-width: 1100px; margin: 32px auto 64px; padding: 0 24px; }}
    .resultaat-info {{ font-size: 0.85rem; color: var(--text-muted); margin-bottom: 20px; }}
    .protocollen-grid {{ display: flex; flex-direction: column; gap: 16px; }}

    .protocol-kaart {{ background: var(--white); border: 1px solid var(--grey-border); border-radius: 14px; padding: 28px 32px; transition: box-shadow 0.2s; }}
    .protocol-kaart:hover {{ box-shadow: 0 4px 20px rgba(44,62,80,0.10); }}
    .protocol-kaart.verborgen {{ display: none; }}
    .zone-badge {{ display: inline-flex; align-items: center; gap: 6px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--oranje); background: var(--oranje-light); padding: 3px 12px; border-radius: 999px; margin-bottom: 12px; }}
    .protocol-naam {{ font-size: 1.05rem; font-weight: 700; color: var(--navy); margin-bottom: 12px; }}
    .protocol-preview {{ font-size: 0.85rem; color: var(--text-muted); line-height: 1.65; margin-bottom: 16px; max-height: 100px; overflow: hidden; position: relative; }}
    .protocol-preview::after {{ content: ""; position: absolute; bottom: 0; left: 0; right: 0; height: 32px; background: linear-gradient(transparent, white); }}
    .protocol-preview h2, .protocol-preview h3 {{ color: var(--navy); font-size: 0.88rem; font-weight: 700; margin-bottom: 4px; margin-top: 8px; }}
    .protocol-preview p {{ margin-bottom: 6px; }}
    .protocol-niveaus {{ display: flex; gap: 8px; flex-wrap: wrap; padding-top: 14px; border-top: 1px solid var(--grey-border); }}
    .niveau-btn {{ padding: 6px 14px; border-radius: 6px; font-size: 0.78rem; font-weight: 600; cursor: pointer; border: none; font-family: inherit; transition: all 0.15s; }}
    .niveau-makkelijk {{ background: #EDF7EE; color: #2e7d32; }}
    .niveau-makkelijk:hover {{ background: #2e7d32; color: white; }}
    .niveau-gemiddeld {{ background: #FEF9E7; color: #B7770D; }}
    .niveau-gemiddeld:hover {{ background: #B7770D; color: white; }}
    .niveau-complex {{ background: #EAF0FB; color: #1A5276; }}
    .niveau-complex:hover {{ background: #1A5276; color: white; }}

    .protocol-viewer {{ margin-top: 20px; border-top: 2px solid var(--oranje-light); padding-top: 16px; }}
    .viewer-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }}
    .viewer-header span {{ font-size: 0.85rem; font-weight: 700; color: var(--oranje); }}
    .viewer-inhoud {{ font-size: 0.9rem; line-height: 1.75; color: var(--text); }}
    .viewer-inhoud h2 {{ font-size: 1rem; font-weight: 700; color: var(--navy); margin: 1em 0 0.4em; }}
    .viewer-inhoud h3 {{ font-size: 0.9rem; font-weight: 700; color: var(--navy); margin: 0.8em 0 0.3em; }}
    .viewer-inhoud p {{ margin-bottom: 0.8em; }}
    .viewer-inhoud ul, .viewer-inhoud ol {{ margin: 0.4em 0 0.8em 1.5em; }}
    .viewer-inhoud li {{ margin-bottom: 0.3em; }}
    .viewer-inhoud table {{ width: 100%; border-collapse: collapse; margin: 1em 0; font-size: 0.85rem; }}
    .viewer-inhoud td, .viewer-inhoud th {{ border: 1px solid var(--grey-border); padding: 6px 10px; text-align: left; }}
    .viewer-inhoud th {{ background: var(--grey-bg); font-weight: 600; }}

    .geen-resultaten {{ text-align: center; padding: 64px 24px; color: var(--text-muted); display: none; }}
    footer {{ background: var(--navy); color: rgba(255,255,255,0.4); text-align: center; padding: 28px 24px; font-size: 0.82rem; }}
    footer a {{ color: rgba(255,255,255,0.6); text-decoration: none; }}
  </style>
</head>
<body>

<header>
  <div class="header-inner">
    <a href="index.html" class="logo">
      <img src="{LOGO_BESTAND}" alt="{SITE_NAAM}" />
      <div class="logo-text"><span>Kansrijk</span> Opgroeien</div>
    </a>
    <nav>
      <a href="protocollen.html">Protocollen</a>
      <a href="index.html#zoeken">Zoeken</a>
      <a href="index.html#specialisaties">Specialisaties</a>
      <a href="mijn-profiel.html">Mijn profiel</a>
      <a href="therapeut-aanmelden.html" class="cta">Aanmelden</a>
    </nav>
  </div>
</header>

<div class="hero">
  <div class="hero-content">
    <h1>Behandelprotocollen<br><em>kinderfysiotherapie</em></h1>
    <p>Wetenschappelijk onderbouwde protocollen voor kinderfysiotherapeuten. Op drie leesniveaus — voor ouders, therapeuten en specialisten.</p>
    <p style="margin-top:14px;font-size:0.78rem;opacity:0.7;max-width:500px;margin-left:auto;margin-right:auto;">⚠️ Deze protocollen zijn algemene informatie. Ze vervangen geen persoonlijk advies van een arts of kinderfysiotherapeut.</p>
    <div class="zoekbalk-wrap" style="margin-top:24px">
      <div class="zoekbalk">
        <input type="text" id="zoek-input" placeholder="Zoek bijv. DCD, motoriek, schrijfproblemen..." oninput="zoek()" />
        <button onclick="zoek()">🔍 Zoeken</button>
      </div>
    </div>
  </div>
</div>

<div class="filter-wrap">
  <span class="filter-label">Specialisatie:</span>
  {zone_filter_btns}
</div>

<div class="container">
  <div class="resultaat-info" id="resultaat-info"></div>
  <div class="protocollen-grid" id="protocollen-grid">
    {protocol_kaarten}
  </div>
  <div class="geen-resultaten" id="geen-resultaten">
    <div style="font-size:3rem;margin-bottom:12px">🔍</div>
    <div>Geen protocollen gevonden voor deze zoekopdracht.</div>
  </div>
</div>

<footer>
  <p>&copy; 2025 {SITE_NAAM} &nbsp;&middot;&nbsp; <a href="index.html">Home</a> &nbsp;&middot;&nbsp; Onderdeel van het <a href="https://vindjefysio.net">VindJeFysio Netwerk</a></p>
</footer>

<script>
  let actieveZone = 'alle';

  function openProtocol(id, niveau) {{
    const kaart  = document.getElementById('kaart-' + id);
    const viewer = document.getElementById('viewer-' + id);
    const inhoud = document.getElementById('viewer-inhoud-' + id);
    const titel  = document.getElementById('viewer-titel-' + id);
    const labels = {{makkelijk:'📗 Makkelijk', gemiddeld:'📘 Gemiddeld', complex:'📕 Complex'}};
    document.querySelectorAll('.protocol-viewer').forEach(v => {{
      if (v.id !== 'viewer-' + id) v.style.display = 'none';
    }});
    try {{
      const htmlData = JSON.parse(kaart.dataset.html.replace(/&quot;/g, '"'));
      inhoud.innerHTML = htmlData[niveau] || '<p>Dit niveau is nog niet beschikbaar.</p>';
      titel.textContent = labels[niveau] || niveau;
      viewer.style.display = 'block';
      viewer.scrollIntoView({{behavior:'smooth', block:'nearest'}});
    }} catch(e) {{
      inhoud.innerHTML = '<p>Protocol kon niet worden geladen.</p>';
      viewer.style.display = 'block';
    }}
  }}

  function sluitProtocol(id) {{
    document.getElementById('viewer-' + id).style.display = 'none';
  }}

  function normaliseer(t) {{
    return t.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }}

  function zoek() {{
    const zoekterm = normaliseer(document.getElementById('zoek-input').value);
    const kaarten  = document.querySelectorAll('.protocol-kaart');
    let zichtbaar  = 0;
    kaarten.forEach(k => {{
      const naam      = normaliseer(k.dataset.naam);
      const tekst     = normaliseer(k.dataset.tekst);
      const zoneMatch = actieveZone === 'alle' || k.dataset.zone === actieveZone;
      const zoekMatch = !zoekterm || naam.includes(zoekterm) || tekst.includes(zoekterm);
      k.classList.toggle('verborgen', !(zoneMatch && zoekMatch));
      if (zoneMatch && zoekMatch) zichtbaar++;
    }});
    document.getElementById('resultaat-info').textContent =
      (zoekterm || actieveZone !== 'alle') ? zichtbaar + ' protocollen gevonden' : '';
    document.getElementById('geen-resultaten').style.display = zichtbaar === 0 ? 'block' : 'none';
  }}

  function filterZone(btn, zone) {{
    actieveZone = zone;
    document.querySelectorAll('.zone-btn').forEach(b => b.classList.remove('actief'));
    btn.classList.add('actief');
    zoek();
  }}
</script>
</body>
</html>'''

with open('protocollen.html', 'w', encoding='utf-8') as f:
    f.write(protocollen_html)
print(f"✓ protocollen.html gegenereerd met {len(protocol_data)} protocollen")

# ─────────────────────────────────────────────────────────────
# SITEMAP
# ─────────────────────────────────────────────────────────────
vandaag = date.today().isoformat()
sitemap_urls = [
    f'  <url><loc>{SITE_URL}/</loc><changefreq>monthly</changefreq><priority>1.0</priority></url>',
    f'  <url><loc>{SITE_URL}/protocollen.html</loc><lastmod>{vandaag}</lastmod><changefreq>weekly</changefreq><priority>0.9</priority></url>',
]
for p in protocol_data:
    for niveau in p['teksten'].keys():
        sitemap_urls.append(
            f'  <url><loc>{SITE_URL}/protocollen/{p["id"]}-{niveau}.html</loc>'
            f'<lastmod>{vandaag}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>'
        )

sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sitemap += '\n'.join(sitemap_urls)
sitemap += '\n</urlset>'

with open('sitemap.xml', 'w', encoding='utf-8') as f:
    f.write(sitemap)
print(f"✓ sitemap.xml gegenereerd met {len(sitemap_urls)} URLs")

if fouten:
    print(f"\n⚠️  {len(fouten)} fout(en):")
    for f in fouten:
        print(f"   – {f}")
else:
    print("\n✅ Klaar zonder fouten!")
