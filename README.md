# MediWatch — Real-Time Patient Safety Monitoring

A real-time, AI-powered patient monitoring agent built on [Stream's Vision Agents SDK](https://getstream.io/video/vision-agents/).
Detects critical safety events (falls, prolonged immobility, distress gestures, IV interference)
and delivers immediate multi-channel alerts to caregivers.

> **⚠️ AI-Assisted Monitoring — Not Diagnostic. All alerts require human verification.**

## Quick Start

```bash
# 1. Clone
git clone https://github.com/your-org/mediwatch
cd mediwatch

# 2. Copy env template
cp .env.example .env
# Fill in your API keys

# 3. Install Python deps
uv sync

# 4. Download YOLO weights
uv run python tools/download_weights.py

# 5. Run backend
uv run python agent/server.py

# 6. In a new terminal, run dashboard
cd dashboard && npm install && npm run dev

# 7. Open http://localhost:5173
```

## Architecture

- **Backend**: Python 3.11+ with Vision Agents SDK, FastAPI, YOLO pose detection
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Privacy**: Raw video never leaves the local machine — only pose keypoints sent to cloud

See [AGENTS.md](AGENTS.md) for full development guidelines and [mediwatch-prd.md](mediwatch-prd.md) for requirements.

## License

MIT
