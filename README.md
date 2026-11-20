# Formule 1-agenda → iOS Agenda

Automatisch bijgewerkte agenda met alle F1-sessies: VT1, VT2, VT3, sprintkwalificatie, sprint, kwalificatie en race.
GitHub Actions haalt elke 6 uur het schema op bij de [Jolpica F1 API](https://github.com/jolpica/jolpica-f1) en GitHub Pages serveert het `.ics`-bestand. Het volgende seizoen verschijnt vanzelf zodra het bekend is.

## Abonneren op iPhone
Instellingen → Agenda → Accounts → Voeg account toe → Overig →
**Voeg agenda-abonnement toe**:
```
https://rashruf.github.io/f1-calendar/f1.ics
```

## Instellingen in deze repo
- **Pages**: Deploy from a branch → `main` / `/docs`.

## Goed om te weten
- Alarmen: race 30 min vooraf, kwalificatie en sprint 15 min vooraf.
- Er wordt alleen gecommit als het schema echt verandert.
- Is een sessietijd nog niet bekend, dan staat er een hele-dag-item met "(tijd volgt)".
