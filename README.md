# Projekt-sportsk-drustvo
Distribuirani sustav za evidenciju članarina i raspored treninga sportskog društva

Projekt prikazuje distribuirani sustav za evidenciju članarina i raspored treninga sportskog društva.
Backend je razvijen u Pythonu korištenjem FastAPI frameworka, a podaci o članovima i terminima pohranjeni su u DynamoDB.
Horizontalna skalabilnost ostvarena je pomoću Nginx alata koji ravnomjerno raspoređuje promet između više instanci servisa.
Sustav omogućuje unos i pregled članova, upravljanje terminima vježbanja te evidenciju članarina po grupama (početni, srednji, napredni
