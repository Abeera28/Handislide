# HandiSlide

Control PowerPoint presentations with hand gestures using your webcam. No extra hardware needed.

## Features

- Navigate slides with hand gestures (swipe, fist, palm)
- Draw and erase annotations directly on PowerPoint slides
- Presenter lock to prevent accidental control from others
- Runs in system tray with visual and audio feedback

## Gestures

| Gesture | Action |
|---------|--------|
| Swipe Right | Next Slide |
| Swipe Left | Previous Slide |
| Fist (hold) | Blackout Screen |
| Open Palm (hold) | Whiteout Screen |
| Thumbs Up | Start Slideshow |
| Thumbs Down | End Slideshow |
| Two Fingers | Toggle Draw Mode |
| Index Finger (draw mode) | Draw |
| Three Fingers | Toggle Erase Mode |
| Index Finger (erase mode) | Erase |
| Fist (draw/erase mode) | Undo |

## Setup

```bash
git clone https://github.com/yourusername/handislide.git
cd handislide
pip install -r requirements.txt
python main.py