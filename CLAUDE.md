# VindJeFysio Netwerk — kansrijkopgroeien.net (Kansrijk Opgroeien)

Deze repo is één "spoke" in een hub-and-spoke netwerk van gespecialiseerde fysiotherapie-subsites. De hub is vindjefysio.net; spokes zijn o.a. rugnek, enkelvoet, beenklachten, mentaalgezond, chronischezorg, armklachten en deze (kansrijkopgroeien).

## Architectuur
- Statische HTML/CSS/vanilla JS op GitHub Pages, custom domein via CNAME.
- Gedeelde Supabase-backend, project islujznszevdynguhjdc, met anon key in de frontend.
- Gedeelde tabellen: therapeuten, praktijken, therapeut_subcategorieen, therapeut_praktijken, subcategorieen, categorieen.
- Elke spoke deelt dezelfde structuur en bestanden: index.html, therapeut-aanmelden.html, mijn-profiel.html, therapeuten.html, privacy.html, protocollen.html (gegenereerd), sync_protocollen.py, .github/workflows/sync-protocollen.yml, protocollen-config.json.

## Belangrijke conventies
- therapeut-aanmelden.html linkt ALTIJD relatief/lokaal binnen de eigen subsite (nooit naar vindjefysio.net).
- Praktijk/locatie-aanmelden loopt WEL centraal via vindjefysio.net/aanmelden.html?via=<domein>.
- Mails lopen via info@vindjefysio.net.
- Therapeut-registratie zet aangemeld_via op het eigen subsite-domein en actief=false (wacht op goedkeuring).
- Deze site: palet primair oranje #E8735A (met oranje-dark #d4614a), navy #2C3E50, secundair groen #4CAF50. In tegenstelling tot de meeste andere spokes heeft deze site géén teal-kleur.
- Deze site richt zich op kinderfysiotherapie/-zorg en werkt (i.p.v. de "DOMEINEN"-groepering die sommige andere spokes gebruiken) met één platte lijst `CATEGORIEEN` (subcategorie-id's 1–10, groep "Kansrijk opgroeien" in de gedeelde subcategorieen-tabel):
  - Motorische ontwikkeling, Schrijven & fijne motoriek, Sport, groei & blessures, Houding & wervelkolom, Ademhaling, Zuigeling & jong kind, Sensorische prikkelverwerking, Revalidatie & operatie, Complexe ontwikkeling, Manuele therapie
- Disciplines op deze site zijn breder dan alleen fysiotherapeut: Fysiotherapeut, Ergotherapeut, Logopedist, Diëtist, Oefentherapeut, Psycholoog.

## Sync-pipeline
- sync_protocollen.py haalt protocollen op uit publiek gedeelde Google Docs (export-link, geen API-key), zet markdown om naar HTML, genereert protocollen/<id>-makkelijk.html (patiënt) en -complex.html (therapeut) + protocollen.html + sitemap.xml.
- De workflow git-add regel moet zijn: git add protocollen/ protocollen.html sitemap.xml (op één regel).
- Google Docs moeten op "iedereen met de link kan bekijken" staan.
