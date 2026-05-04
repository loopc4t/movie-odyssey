# Movie Odyssey 🎬

A keyboard-driven terminal film manager for your local library.
Psychotronic cult-cinema aesthetic. Vim navigation. iPod click wheel sound.

## Requirements

- Python 3.10+
- `mpv` — plays the films, inhibits idle/sleep on Wayland
- `mpg123` — click sound (`sudo apt install mpg123`)
- Movies organised as TinyMediaManager folders under `~/Videos/Movies/`

## Installation

```bash
# Add alias to ~/.bashrc
echo "alias movie_odyssey='python3 ~/Projects/movie_odyssey/movie_odyssey.py'" >> ~/.bashrc && source ~/.bashrc
```

Then just type `movie_odyssey` to launch.

## Expected folder structure

```
~/Videos/Movies/
└── Alien (1979)/
    ├── Alien (1979).mp4
    ├── Alien (1979).nfo        ← TinyMediaManager NFO (Kodi format)
    ├── Alien (1979)-poster.jpg
    └── Alien (1979)-fanart.jpg
```

## Keyboard Reference

### Navigation

| Key               | Action                            |
|-------------------|-----------------------------------|
| `j` / `↓`         | Move down 1                       |
| `k` / `↑`         | Move up 1                         |
| `h` / `←`         | Jump 10 up                        |
| `l` / `→`         | Jump 10 down                      |
| `Ctrl-D`          | Half page down                    |
| `Ctrl-U`          | Half page up                      |
| `Ctrl-F` / `PgDn` | Full page down                    |
| `Ctrl-B` / `PgUp` | Full page up                      |
| `gg`              | Jump to top                       |
| `G`               | Jump to bottom                    |
| `[N]j` / `[N]k`  | Move N rows (e.g. `10j`, `5k`)    |
| `[N]G`            | Jump to title N (e.g. `42G`)      |

### Actions

| Key           | Action                      |
|---------------|-----------------------------|
| `Enter` / `p` | Play selected film          |
| `/` or `f`    | Enter search / filter mode  |
| `Esc`         | Exit search mode            |
| `q`           | Quit                        |

### List indicators

| Symbol | Meaning                  |
|--------|--------------------------|
| `>`    | Film has a playable file |
| `*`    | Film has NFO metadata    |

While in **search mode** just type to filter; the list updates live.
Press `Esc` or `Enter` to return to normal navigation.

## Sound

Scroll sounds are played via a persistent `mpg123 --remote` server process.
The binary loads once at startup, so clicks fire with near-zero latency.
Place your `click.mp3` in the same folder as the scripts.

## Sleep inhibition

When playing a film, Movie Odyssey prevents the screen from sleeping via:

1. `gnome-session-inhibit` — preferred on Wayland/GNOME
2. `systemd-inhibit` — fallback
3. bare `mpv` — last resort (no inhibition)

To check which one your system uses:

```bash
which gnome-session-inhibit
which systemd-inhibit
```

## Files

| File               | Purpose                                    |
|--------------------|--------------------------------------------|
| `movie_odyssey.py` | Entry point                                |
| `ui.py`            | Curses TUI — list, info panel, navigation  |
| `library.py`       | Scan `~/Videos/Movies/`, locate video/nfo |
| `nfo_parser.py`    | Parse TinyMediaManager XML `.nfo` files    |
| `player.py`        | Launch mpv with idle inhibition            |
| `click.mp3`        | Scroll click sound                         |
