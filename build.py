"""Bouwt docs/f1.ics met alle F1-sessies (VT1-3, sprint, kwalificatie, race).

Bron: Jolpica F1 API (opvolger van Ergast). Alleen standaardbibliotheek.
Haalt het huidige seizoen en, zodra beschikbaar, het volgende seizoen op.
"""
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API = "https://api.jolpi.ca/ergast/f1/{season}.json?limit=100"
OUT = Path(__file__).parent / "docs" / "f1.ics"

# (sleutel in API, korte naam, duur in minuten, alarm in minuten vooraf of None)
SESSIONS = [
    ("FirstPractice", "VT1", 60, None),
    ("SecondPractice", "VT2", 60, None),
    ("ThirdPractice", "VT3", 60, None),
    ("SprintQualifying", "Sprintkwalificatie", 45, None),
    ("Sprint", "Sprint", 60, 15),
    ("Qualifying", "Kwalificatie", 60, 15),
    ("Race", "Race", 120, 30),
]
ICONS = {"Race": "🏁", "Kwalificatie": "⏱️", "Sprint": "⚡", "Sprintkwalificatie": "⏱️"}


def fetch(season):
    req = urllib.request.Request(API.format(season=season), headers={"User-Agent": "f1-calendar (github.com/rashruf/f1-calendar)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)["MRData"]["RaceTable"]["Races"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        raise


def esc(text):
    return str(text).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line):
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    parts, cur = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        if len(cur) + len(b) > (75 if not parts else 74):
            parts.append(cur.decode("utf-8"))
            cur = b""
        cur += b
    parts.append(cur.decode("utf-8"))
    return "\r\n ".join(parts)


def utc(dt):
    return dt.strftime("%Y%m%dT%H%M%SZ")


def events_for(race):
    gp = race["raceName"].replace("Grand Prix", "GP")
    c = race["Circuit"]
    loc = f'{c["circuitName"]}, {c["Location"]["locality"]}, {c["Location"]["country"]}'
    sessions = dict(race)
    sessions["Race"] = {"date": race["date"], "time": race.get("time")}
    for key, name, minutes, alarm in SESSIONS:
        s = sessions.get(key)
        if not isinstance(s, dict) or not s.get("date"):
            continue
        ev = {
            "uid": f'f1-{race["season"]}-{int(race["round"]):02d}-{key.lower()}@rashruf.github.io',
            "summary": f'{ICONS.get(name, "🏎️")} F1 {name} – {gp}',
            "location": loc,
            "description": f'Ronde {race["round"]} van het {race["season"]} F1-seizoen\n{race.get("url", "")}',
            "alarm": alarm,
        }
        if s.get("time"):
            start = datetime.fromisoformat(f'{s["date"]}T{s["time"].replace("Z", "")}').replace(tzinfo=timezone.utc)
            ev["start"], ev["end"] = start, start + timedelta(minutes=minutes)
        else:  # tijd nog niet bekend → hele dag
            ev["date"] = s["date"].replace("-", "")
            ev["summary"] += " (tijd volgt)"
        yield ev


def build(races):
    now = utc(datetime.now(timezone.utc))
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//rashruf//f1-calendar//NL", "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH", "X-WR-CALNAME:Formule 1", "X-WR-TIMEZONE:Europe/Amsterdam",
        "REFRESH-INTERVAL;VALUE=DURATION:PT6H", "X-PUBLISHED-TTL:PT6H",
    ]
    count = 0
    for race in races:
        for ev in events_for(race):
            count += 1
            lines += ["BEGIN:VEVENT", f'UID:{ev["uid"]}', f"DTSTAMP:{now}"]
            if "start" in ev:
                lines += [f'DTSTART:{utc(ev["start"])}', f'DTEND:{utc(ev["end"])}']
            else:
                d = datetime.strptime(ev["date"], "%Y%m%d")
                lines += [f'DTSTART;VALUE=DATE:{ev["date"]}', f'DTEND;VALUE=DATE:{(d + timedelta(days=1)):%Y%m%d}']
            lines += [f'SUMMARY:{esc(ev["summary"])}', f'LOCATION:{esc(ev["location"])}',
                      f'DESCRIPTION:{esc(ev["description"])}', "TRANSP:TRANSPARENT"]
            if ev["alarm"] and "start" in ev:
                lines += ["BEGIN:VALARM", "ACTION:DISPLAY", f'DESCRIPTION:{esc(ev["summary"])}',
                          f'TRIGGER:-PT{ev["alarm"]}M', "END:VALARM"]
            lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in lines) + "\r\n", count


def main():
    year = datetime.now(timezone.utc).year
    races = []
    for season in (year, year + 1):
        got = fetch(season)
        print(f"Seizoen {season}: {len(got)} races")
        races += got
    if not races:
        sys.exit("Geen races ontvangen — bestaande agenda blijft staan.")
    ics, n = build(races)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(ics, encoding="utf-8", newline="")
    print(f"{n} sessies geschreven naar {OUT}")


if __name__ == "__main__":
    main()
