# ⚡ AthleteView Pro
### The World's First Hybrid Wearable Camera + Biometric Broadcast Platform

> **See the game from inside the athlete. Feel every heartbeat.**

![Status](https://img.shields.io/badge/Status-Pre--Seed%20Build-orange) ![Stage](https://img.shields.io/badge/Stage-Prototype%20Design-blue) ![Location](https://img.shields.io/badge/HQ-Chennai%2C%20India-green) ![License](https://img.shields.io/badge/License-Proprietary-red)

---

## 🎯 What is AthleteView Pro?

AthleteView Pro is a **hybrid wearable camera system** embedded in an athlete's jersey/patch that delivers:
- **Live first-person POV video** from every player simultaneously
- **Real-time biometric data** (Heart Rate, SpO2, Skin Temp, Motion) overlaid on broadcast
- **AI-powered 3D Gaussian Splatting** for free-viewpoint replays
- **Self-hosted streaming** to your own platform + simultaneous broadcast to TV/OTT channels
- **Sub-300ms ultra-low-latency** live delivery via SRT protocol

---

## 📁 Repository Structure

```
athletview-pro/
├── docs/
│   ├── 01-PRODUCT-SPEC.md          # Full hardware specifications
│   ├── 02-PROCUREMENT.md           # Supplier contacts, pricing, BOM
│   ├── 03-AI-MODEL-ARCHITECTURE.md # AI/ML pipeline specs
│   ├── 04-STREAMING-ARCHITECTURE.md# Streaming platform design
│   ├── 05-BUSINESS-PLAN.md         # GTM, revenue, fundraising
│   ├── 06-COMPETITOR-ANALYSIS.md   # Why others failed, our moat
│   └── 07-USE-CASES.md             # 10 detailed use cases
├── firmware/
│   ├── main-cam/                   # RV1106 firmware for Main Cam
│   └── patch-cam/                  # RV1103 firmware for Patch Cam
├── ai-models/
│   ├── player-detection/           # YOLOv10 + BoT-SORT tracking
│   ├── 3dgs-pipeline/              # LiveSplats 3D Gaussian Splatting
│   └── biometric-fusion/           # HR/SpO2 signal processing
├── streaming-platform/
│   ├── ingest-server/              # SRT ingest + media server
│   ├── web-player/                 # React + WebGL viewer
│   └── tv-broadcast/               # HLS/RTMP broadcast output
├── website/
│   ├── landing/                    # Marketing website (Next.js)
│   └── dashboard/                  # Analytics dashboard
└── README.md
```

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FIELD LAYER (On-Athlete)                      │
│                                                                  │
│  ┌──────────────────┐    ┌──────────┐    ┌──────────┐           │
│  │   MAIN CAM (1x)  │    │PATCH CAM │    │PATCH CAM │  ...      │
│  │  Chest/Sternum   │    │  (2x)    │    │  (3x)    │           │
│  │                  │    │ Shoulder │    │  Back    │           │
│  │ Sony IMX577 12MP │    │IMX307 2MP│    │IMX307 2MP│           │
│  │ RV1106 SoC       │    │RV1103SoC │    │RV1103SoC │           │
│  │ MAX86141 (HR/SpO2│    │Video only│    │Video only│           │
│  │ MAX30208 (Temp)  │    │          │    │          │           │
│  │ ICM42688 (IMU)   │    │          │    │          │           │
│  │ 5G/WiFi6 TX      │    │BLE Mesh  │    │BLE Mesh  │           │
│  └──────────────────┘    └──────────┘    └──────────┘           │
│           │                    │               │                 │
│           └────────────────────┴───────────────┘                │
│                        BLE 5.3 Mesh → Main Cam                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ SRT (5G / WiFi 6)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EDGE SERVER (At Venue)                         │
│  NVIDIA Jetson Orin NX 16GB                                     │
│  ├── SRT Ingest + Sync (all camera streams)                     │
│  ├── YOLOv10 + BoT-SORT Player Detection                       │
│  ├── Cross-Camera ReID (ViT embeddings)                         │
│  └── LiveSplats 3DGS Real-time Reconstruction                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
         ┌─────────┐ ┌────────┐ ┌──────────┐
         │AthleteView│ │TV/OTT  │ │Social /  │
         │Platform   │ │Channels│ │YouTube/  │
         │(own CDN)  │ │RTMP out│ │Twitch    │
         └─────────┘ └────────┘ └──────────┘
```

---

## 🔧 Quick Links

- [📋 Full Product Spec](docs/01-PRODUCT-SPEC.md)
- [🛒 Procurement Guide](docs/02-PROCUREMENT.md)
- [🤖 AI Model Architecture](docs/03-AI-MODEL-ARCHITECTURE.md)
- [📡 Streaming Architecture](docs/04-STREAMING-ARCHITECTURE.md)
- [📈 Business Plan](docs/05-BUSINESS-PLAN.md)
- [⚔️ Competitor Analysis](docs/06-COMPETITOR-ANALYSIS.md)
- [🎮 Use Cases](docs/07-USE-CASES.md)

---

## 🚀 Competitive Moat

| Feature | AthleteView Pro | FirstV1sion | Intel True View | Hawk-Eye |
|---------|----------------|-------------|-----------------|----------|
| Wearable camera | ✅ | ✅ | ❌ | ❌ |
| Multi-patch (3+ cams/player) | ✅ | ❌ | ❌ | ❌ |
| HR + SpO2 live on broadcast | ✅ | Partial | ❌ | ❌ |
| 3DGS free-viewpoint replay | ✅ | ❌ | ✅ (fixed) | ❌ |
| Own streaming platform | ✅ | ❌ | ❌ | ❌ |
| Under $80 BOM per athlete | ✅ | ❌ (>$500) | ❌ ($2M+/venue) | ❌ |
| India-first GTM | ✅ | ❌ | ❌ | ❌ |

---

## 💰 Funding Ask

| Round | Amount | Use | Timeline |
|-------|--------|-----|----------|
| Pre-Seed | ₹1.5 Cr ($180K) | 5 prototypes, IP filing, pilot | Month 0–6 |
| Seed | ₹8 Cr ($960K) | 100-unit production, platform | Month 6–18 |
| Series A | ₹40 Cr ($4.8M) | Scale to 5 leagues | Month 18–36 |

---

## 👤 Founder

**Pradhap** — Product Builder, Chennai, India
Building AthleteView Pro with AI-first product methodology.

---

*Built with ❤️ in Chennai, India | © 2026 AthleteView Pro*
