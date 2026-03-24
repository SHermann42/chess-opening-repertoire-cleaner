# opening-cut-replace-mistakes

Python-Skript zum Analysieren von PGN-Partien mit Stockfish.

Das Skript durchsucht jede Partie nach dem **ersten Fehler einer gewählten Farbe**, schneidet die Partie **genau an dieser Stelle ab** und ersetzt den fehlerhaften Zug durch den **besten von Stockfish gefundenen Zug**.

Die aktuelle Fassung enthält zusätzliche Schutzmechanismen gegen scheinbare Hänger:
- harter UCI-Timeout für Stockfish
- optionaler automatischer Engine-Neustart nach jeweils `N` Partien
- Debug-Ausgaben für laufende Partie und Halbzug
- robustere Behandlung von Engine-Fehlern

## Funktionen

- Analyse nur für eine gewählte Farbe: `--color white|black`
- Fehlersuche beginnt erst ab einem bestimmten Zug dieser Farbe: `--start-move`
- Fehlerdefinition über Centipawn-Schwelle: `--threshold-cp`
- Begrenzung der Analyse auf die ersten `N` Halbzüge: `--max-ply`
- Fortschrittsanzeige mit `tqdm`
- Optionales Beibehalten unveränderter Partien in der Ausgabe
- Optionales Kommentieren des ersetzten Zuges in der Ausgabe-PGN
- Harter Engine-Timeout über `--engine-timeout`
- Optionaler Engine-Neustart nach jeweils `N` Partien über `--restart-engine-every`
- Zusätzliche Debug-Ausgaben über `--debug-progress`

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
````

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

* Linux: `/usr/games/stockfish`
* macOS: `/opt/homebrew/bin/stockfish`
* Windows: `C:\\Tools\\stockfish\\stockfish-windows-x86-64.exe`

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

### Empfohlener robuster Start

Für größere PGN-Dateien ist diese Variante sinnvoll:

```bash
python opening_cut_replace_mistakes.py \
  --input games.pgn \
  --output output.pgn \
  --engine /usr/games/stockfish \
  --depth 12 \
  --color black \
  --max-ply 60 \
  --engine-timeout 15 \
  --restart-engine-every 100 \
  --debug-progress
```

## Beispiele

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

### Beispiel 4: Robuste Analyse mit Timeout und Engine-Neustart

```bash
python opening_cut_replace_mistakes.py \
  --input games.pgn \
  --output repaired_games.pgn \
  --engine /usr/games/stockfish \
  --depth 14 \
  --color black \
  --engine-timeout 15 \
  --restart-engine-every 100 \
  --debug-progress
```

### Beispiel 5: Debug-Ausgabe bei langen oder problematischen Partien

```bash
python opening_cut_replace_mistakes.py \
  --input games.pgn \
  --output repaired_games.pgn \
  --engine /usr/games/stockfish \
  --movetime-ms 250 \
  --color white \
  --debug-progress \
  --debug-every-ply 10
```

## Wichtige Parameter

### Pflichtparameter

* `--input` – Eingabe-PGN
* `--output` – Ausgabe-PGN
* `--engine` – Pfad zur Stockfish-Binary
* **genau einer** von:

  * `--depth`
  * `--movetime-ms`
  * `--nodes`

### Optionale Parameter

* `--color white|black` – zu analysierende Farbe, Standard: `black`
* `--threshold-cp` – Fehlerschwelle in Centipawns, Standard: `40`
* `--start-move` – erst ab Zug X der analysierten Farbe prüfen, Standard: `1`
* `--max-ply` – nur die ersten N Halbzüge prüfen
* `--keep-unmodified` – unveränderte Partien ebenfalls in die Ausgabe schreiben
* `--no-annotate` – keinen Kommentar am ersetzten Zug anhängen
* `--hash-mb` – Stockfish-Hash in MB
* `--threads` – Anzahl Stockfish-Threads
* `--no-progress` – Fortschrittsanzeige deaktivieren
* `--engine-timeout` – harter UCI-Timeout in Sekunden, Standard: `15.0`
* `--restart-engine-every` – Engine nach jeweils `N` Partien neu starten, `0` deaktiviert den Neustart, Standard: `100`
* `--debug-progress` – zusätzliche Statusmeldungen zu aktueller Partie und laufender Analyse auf `stderr`
* `--debug-every-ply` – bei Debug-Ausgaben Meldung alle `N` analysierten Halbzüge, Standard: `20`

## Bedeutung der neuen Stabilitätsoptionen

### `--engine-timeout`

Setzt einen harten Timeout für die Kommunikation mit der UCI-Engine.
Das schützt gegen Situationen, in denen die Analyse bei einzelnen Stellungen scheinbar hängen bleibt.

Beispiel:

```bash
--engine-timeout 15
```

### `--restart-engine-every`

Startet Stockfish regelmäßig neu.
Das ist bei sehr langen Runs sinnvoll, um problematische Engine-Zustände oder Kommunikationsfehler abzufangen.

Beispiele:

```bash
--restart-engine-every 100
--restart-engine-every 0
```

* `100` = Neustart nach jeweils 100 Partien
* `0` = deaktiviert

### `--debug-progress`

Schreibt zusätzliche Diagnosemeldungen nach `stderr`, z. B.:

* Start einer neuen Partie
* Engine-Neustart
* laufende Analyse bei Halbzug X
* Fehler beim Analysieren einer Partie

Das hilft zu unterscheiden, ob das Skript wirklich hängt oder nur an einer langen Partie arbeitet.

## Ausgabe

Das Skript schreibt eine neue PGN-Datei.

Verhalten:

* Bei gefundener Fehlstelle wird die Partie **vor dem Fehler abgeschnitten**.
* Der fehlerhafte Zug wird durch den **besten Stockfish-Zug** ersetzt.
* Der Rest der Originalpartie wird **nicht übernommen**.
* `Result` wird auf `*` gesetzt.
* Optional wird ein Kommentar mit Vergleich zwischen gespieltem Zug und Ersatz-Zug eingefügt.

## Verhalten bei Engine-Fehlern oder Timeouts

Die aktuelle Fassung behandelt problematische Partien robuster:

* Wenn eine Partie wegen Timeout, Engine-Abbruch oder UCI-Fehler nicht analysiert werden kann, wird sie als Fehler gezählt.
* Danach versucht das Skript, die Engine neu zu starten.
* Wenn `--keep-unmodified` gesetzt ist, wird die betroffene Originalpartie trotzdem in die Ausgabe geschrieben.
* Die Verarbeitung der restlichen PGN-Datei läuft weiter.

Das verhindert, dass ein einzelner problematischer Fall den gesamten Lauf stoppt.

## Beispiel für den Kommentar in der PGN

```text
Black error replaced. played: ... , best continuation: ... , evaluation played: -0.35, best: 0.20, difference: 0.55 pawns.
```

## Typische Anwendungsfälle

* Eröffnungsrepertoire aus PGNs „säubern“
* Trainingsdaten für Opening-Lines vorbereiten
* Erste grobe Fehler einer Seite automatisch korrigieren
* Variantenbäume aus realen Partien mit engine-korrigierten Fortsetzungen erzeugen

## Bekannte Grenzen

* Das Skript ersetzt **nur den ersten** gefundenen Fehler pro Partie.
* Die Qualität der Ergebnisse hängt stark von den Engine-Einstellungen ab.
* Bei sehr großen PGN-Dateien kann die Analyse je nach Tiefe, Zeit oder Knotenzahl lange dauern.
* Einzelne schwierige oder problematische Stellungen können trotz Schutzmechanismen langsamer sein als der Rest.
* Der Kommentartext im PGN ist derzeit englischsprachig.
* Das Skript analysiert Partien sequentiell, nicht parallel.

## Tipps für große PGN-Dateien

Für stabile Läufe auf großen Sammlungen sind diese Einstellungen sinnvoll:

* moderate Tiefe statt sehr hoher Tiefe
* `--max-ply`, wenn nur die Eröffnung relevant ist
* `--engine-timeout 15`
* `--restart-engine-every 100`
* `--debug-progress`, wenn du prüfen willst, an welcher Partie das Skript gerade arbeitet

Ein praxisnaher Start ist:

```bash
python opening_cut_replace_mistakes.py \
  --input games.pgn \
  --output output.pgn \
  --engine /usr/games/stockfish \
  --depth 12 \
  --color black \
  --max-ply 60 \
  --engine-timeout 15 \
  --restart-engine-every 100 \
  --debug-progress
```

## Lizenz

Dieses Projekt steht unter der **GNU GPL v3**. Details siehe Datei `LICENSE`.

## Autor

**Dr. Sven Hermann**
