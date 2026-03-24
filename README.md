# opening-cut-replace-mistakes

Python-Skript zum Analysieren von PGN-Partien mit Stockfish.

Das Skript durchsucht jede Partie nach dem **ersten Fehler einer gewählten Farbe**, schneidet die Partie **genau an dieser Stelle ab** und ersetzt den fehlerhaften Zug durch den **besten von Stockfish gefundenen Zug**.

## Funktionen

- Analyse nur für eine gewählte Farbe: `--color white|black`
- Fehlersuche beginnt erst ab einem bestimmten Zug dieser Farbe: `--start-move`
- Fehlerdefinition über Centipawn-Schwelle: `--threshold-cp`
- Begrenzung der Analyse auf die ersten `N` Halbzüge: `--max-ply`
- Fortschrittsanzeige mit `tqdm`
- Optionales Beibehalten unveränderter Partien in der Ausgabe
- Optionales Kommentieren des ersetzten Zuges in der Ausgabe-PGN

## Definition eines Fehlers

Ein Zug gilt als Fehler, wenn es einen alternativen legalen Zug gibt, den Stockfish um mindestens `threshold_cp` Centipawns besser bewertet als den tatsächlich gespielten Zug.

## Voraussetzungen

- Python **3.10+**
- Eine installierte **Stockfish**-Binary
- Python-Pakete aus `requirements.txt`

## Installation

### 1. Repository klonen

```bash
git clone https://github.com/SHermann42/opening-cut-replace-mistakes.git
cd opening-cut-replace-mistakes
```

### 2. Virtuelle Umgebung anlegen

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Windows (PowerShell)**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Stockfish installieren

Du brauchst eine lokale Stockfish-Binary und musst ihren Pfad per `--engine` angeben.

Beispiele:

- Linux: `/usr/games/stockfish`
- macOS: `/opt/homebrew/bin/stockfish`
- Windows: `C:\\Tools\\stockfish\\stockfish-windows-x86-64.exe`

## Verwendung

Grundform:

```bash
python opening_cut_replace_mistakes.py \
  --input input.pgn \
  --output output.pgn \
  --engine /pfad/zu/stockfish \
  --depth 18 \
  --color black
```

### Beispiel 1: Schwarze Fehler ab Zug 8 suchen

```bash
python opening_cut_replace_mistakes.py \
  --input games.pgn \
  --output black_repaired_from_move8.pgn \
  --engine /usr/games/stockfish \
  --depth 18 \
  --color black \
  --start-move 8 \
  --threshold-cp 40
```

### Beispiel 2: Weiße Fehler mit fixer Rechenzeit analysieren

```bash
python opening_cut_replace_mistakes.py \
  --input games.pgn \
  --output white_repaired.pgn \
  --engine /usr/games/stockfish \
  --movetime-ms 300 \
  --color white \
  --start-move 6 \
  --threshold-cp 60 \
  --keep-unmodified
```

### Beispiel 3: Analyse nur in der Eröffnung

```bash
python opening_cut_replace_mistakes.py \
  --input games.pgn \
  --output opening_only.pgn \
  --engine /usr/games/stockfish \
  --nodes 50000 \
  --color black \
  --max-ply 30
```

## Wichtige Parameter

### Pflichtparameter

- `--input` – Eingabe-PGN
- `--output` – Ausgabe-PGN
- `--engine` – Pfad zur Stockfish-Binary
- **genau einer** von:
  - `--depth`
  - `--movetime-ms`
  - `--nodes`

### Optionale Parameter

- `--color white|black` – zu analysierende Farbe, Standard: `black`
- `--threshold-cp` – Fehlerschwelle in Centipawns, Standard: `40`
- `--start-move` – erst ab Zug X der analysierten Farbe prüfen, Standard: `1`
- `--max-ply` – nur die ersten N Halbzüge prüfen
- `--keep-unmodified` – unveränderte Partien ebenfalls in die Ausgabe schreiben
- `--no-annotate` – keinen Kommentar am ersetzten Zug anhängen
- `--hash-mb` – Stockfish-Hash in MB
- `--threads` – Anzahl Stockfish-Threads
- `--no-progress` – Fortschrittsanzeige deaktivieren

## Ausgabe

Das Skript schreibt eine neue PGN-Datei.

Verhalten:

- Bei gefundener Fehlstelle wird die Partie **vor dem Fehler abgeschnitten**.
- Der fehlerhafte Zug wird durch den **besten Stockfish-Zug** ersetzt.
- Der Rest der Originalpartie wird **nicht übernommen**.
- `Result` wird auf `*` gesetzt.
- Optional wird ein Kommentar mit Vergleich zwischen gespieltem Zug und Ersatz-Zug eingefügt.

## Beispiel für den Kommentar in der PGN

```text
Black error replaced. played: ... , best continuation: ... , evaluation played: -0.35, best: 0.20, difference: 0.55 pawns.
```

## Typische Anwendungsfälle

- Eröffnungsrepertoire aus PGNs „säubern"
- Trainingsdaten für Opening-Lines vorbereiten
- Erste grobe Fehler einer Seite automatisch korrigieren
- Variantenbäume aus realen Partien mit engine-korrigierten Fortsetzungen erzeugen

## Bekannte Grenzen

- Das Skript ersetzt **nur den ersten** gefundenen Fehler pro Partie.
- Die Qualität der Ergebnisse hängt stark von den Engine-Einstellungen ab.
- Bei sehr großen PGN-Dateien kann die Analyse je nach Tiefe/Zeit/Nodes lange dauern.
- Der Kommentartext im PGN ist derzeit englischsprachig.

## Lizenz

Dieses Projekt steht unter der **GNU GPL v3**. Details siehe Datei `LICENSE`.

## Autor

**Dr. Sven Hermann**
