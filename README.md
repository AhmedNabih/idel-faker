# idel-faker

Windows system-tray tool that keeps Microsoft Teams showing "Available" by
injecting invisible input (F15 + 1px mouse nudge) only when you are genuinely
idle. Stays silent while you work. Turns the tray icon orange when the screen is
locked (a state no user-space tool can defeat).

## Install

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```
python -m idel_faker.tray
```

Tray icon: green = active, grey = paused, orange = locked (you are Away).
Right-click for Pause/Resume and Quit.

## Config

Edit constants at the top of `idel_faker/tray.py`:
- `IDLE_THRESHOLD` (seconds idle before injecting, default 60)
- `POLL_INTERVAL` (seconds between checks, default 5)

## Limitations

Cannot keep you "Available" while the workstation is locked (Win+L or GPO
auto-lock) — injected input is not registered as session activity when locked.
The tool reports this honestly via the orange icon.

## Development

```
pip install -r requirements-dev.txt
pytest
```
