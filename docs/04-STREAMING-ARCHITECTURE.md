# 📡 Streaming Architecture - AthleteView Pro

> Own platform + TV channels + social streaming, all simultaneously

---

## STREAMING OVERVIEW

AthleteView streams in 3 directions simultaneously:
1. **AthleteView Platform** - Own CDN, 6-DOF 3DGS viewer, subscription fans
2. **TV Broadcast** - RTMP/SRT to any broadcaster (Star Sports, JioCinema, Sky Sports)
3. **Social Platforms** - RTMP to YouTube Live, Twitch, Instagram Live

---

## INGEST LAYER (Stadium Edge Server)

### Hardware
```
NVIDIA Jetson Orin NX 16GB
Intel NUC 13 Pro (backup ingest server)
Mellanox 10GbE NIC (stadium WiFi 6 uplink)
```

### SRT Ingest Configuration
```yaml
# MediaMTX config for multi-stream SRT ingest
paths:
  main-cam-player-1:
    source: srt://0.0.0.0:8890?streamid=player1-main&latency=200
    sourceProtocol: srt
  patch-cam-player-1-shoulder:
    source: srt://0.0.0.0:8891?streamid=player1-patch1&latency=200
    sourceProtocol: srt
  # ... repeat for all 22 players x 3 cams = 66 paths

# Total bandwidth required (22 players x 3 cams x 8Mbps = 528 Mbps)
# Stadium WiFi 6: 9.6 Gbps peak -> comfortable headroom
```

### Synchronization
```
Method: IEEE 1588 PTP (Precision Time Protocol)
Accuracy: <1ms inter-stream sync
Implementation: PTP4L daemon on Jetson
Fallback: NTP-based sync with <5ms accuracy

Why critical: 3DGS reconstruction requires frame-accurate multi-view sync
```

---

## PROCESSING LAYER

### Pipeline
```
SRT Ingest (66 streams)
    |
    v
Stream Multiplexer (FFmpeg)
    |
    v
[PARALLEL PROCESSING]
    |           |           |
    v           v           v
AI Layer    Broadcast    Biometric
(3DGS +     Mixing       Overlay
 tracking)  Engine       Engine
    |           |           |
    v           v           v
[OUTPUTS]
```

### Broadcast Mixing Engine
```
Inputs: All 66 streams
Functions:
  - Director mode: Manual stream selection UI
  - Auto mode: AI picks best angle based on action detection
  - Overlay injection: HR, SpO2, speed data on any stream
  - PiP (Picture in Picture): Main broadcast + POV in corner
  - Replay injection: 3DGS replay at key moments

Software: Custom NodeJS + FFmpeg pipeline
Latency added: <50ms
```

---

## OUTPUT LAYER

### Output 1: AthleteView Platform (Own CDN)
```
Protocol: HLS (HTTP Live Streaming)
Latency: 3-6 seconds (HLS standard)
Resolutions: 1080p, 720p, 480p, 360p (adaptive bitrate)
Server: AWS CloudFront CDN
WebRTC option: <500ms latency for premium subscribers

Special features:
  - 3DGS viewer: WebGL-based, .splat format streaming via WebSocket
  - Multi-camera switcher: Fans can pick their favorite player's cam
  - Biometric timeline: Scrubable HR/SpO2 chart synchronized with video
  - Clip sharing: Auto-generated highlight clips with biometric overlay

Cost at scale:
  - 100K concurrent viewers: ~$400/match (CloudFront)
  - With client-side 3DGS rendering: Save 70% GPU cost
```

### Output 2: TV Broadcast (Star Sports / Sky Sports / others)
```
Protocol: SRT or RTMP (broadcaster preference)
Latency: 150-300ms (SRT) or 500ms (RTMP)
Format: Single mixed stream (director-selected angle) OR
        Multiple raw streams for broadcaster's own switching

Integration options:
  Option A: Full service - AthleteView provides 1 mixed broadcast-ready stream
  Option B: Data layer only - Broadcaster gets:
            - 22x raw SRT POV streams
            - Live biometric data JSON feed
            - 3DGS replay endpoint for replay moments

Broadcast chain:
  AthleteView Edge Server
    -> Contribution SRT (100Mbps uplink from venue)
      -> Broadcaster OB Van / Satellite uplink
        -> TV Transmission -> Fan TV

Latency on TV: 4-8 seconds (standard broadcast delay)
```

### Output 3: Social Platforms
```
Protocol: RTMP
Targets: YouTube Live, Twitch, Instagram Live, Facebook Live

Simultaneous streaming (multi-platform):
  - Software: Restream.io or custom RTMP splitter
  - Bitrate: 6-8 Mbps (YouTube), 6 Mbps (Twitch), 4 Mbps (Instagram)

Content strategy:
  - YouTube: Full match POV stream (1 player's angle, fan voted)
  - Twitch: Interactive stream with real-time biometric chat integration
  - Instagram: Highlight clips auto-pushed after key moments
```

---

## PROTOCOL COMPARISON

| Protocol | Latency | Use Case | Our Usage |
|----------|---------|----------|-----------|
| SRT | 150-300ms | Contribution, broadcast | Cam to edge server, edge to broadcaster |
| RTMP | 500ms-2s | Social platforms | YouTube, Twitch, Instagram |
| HLS | 3-6s | Mass consumption CDN | AthleteView platform |
| WebRTC | 100-200ms | Ultra-low latency web | Premium platform subscribers |
| RIST | 200-400ms | Broadcast alternative to SRT | Enterprise broadcaster option |

---

## LATENCY BUDGET

```
Camera capture                    : 0ms (reference)
H.265 encode on RV1106            : +30ms
SRT transmission (WiFi 6)         : +50ms
Edge server ingest                : +20ms
AI processing (detection/overlay) : +80ms
Stream mixing                     : +20ms
                                  --------
Total to edge server output       : ~200ms

Edge to Platform (HLS)            : +3000-5000ms
Edge to Broadcaster (SRT)         : +150-300ms
Edge to Social (RTMP)             : +500-2000ms
Edge to WebRTC premium            : +50ms
```

---

## INFRASTRUCTURE SIZING

### Per-Match Compute (Edge)
| Component | Spec | Cost/match |
|-----------|------|------------|
| Jetson Orin NX 16GB | On-site | ₹0 (capex) |
| 5G data (backup uplink) | 50GB | ₹500 |
| Stadium WiFi 6 | Venue-provided | ₹0 |

### Per-Match Cloud
| Component | Spec | Cost/match |
|-----------|------|------------|
| AWS CloudFront | 100K viewers | $400 |
| S3 storage (clips) | 50GB/match | $1.15 |
| EC2 inference (AI) | g5.xlarge 4hr | $4 |
| **Total cloud/match** | | **~$405** |

### Revenue vs Cost
```
At 100K viewers:
  Revenue (subs): 50K x ₹299/month / 10 matches = ₹14,95,000 = ~$18K/match
  Cloud cost: $405/match
  Gross margin: 97.8% on streaming revenue
```

---

## WEBSITE + PLATFORM TECH STACK

### Marketing Website
```
Framework: Next.js 14 (App Router)
Styling: Tailwind CSS + Framer Motion
Hosting: Vercel
Features:
  - 3D product animation (Three.js)
  - Sample football POV video (WebM autoplay)
  - Before/after broadcast comparison
  - Live biometric overlay demo (interactive)
  - Investor deck download
  - League partnership inquiry form
```

### Fan Platform (Web App)
```
Frontend: React + Three.js (3DGS viewer)
Backend: Node.js + FastAPI (Python for AI)
Database: PostgreSQL (user data) + InfluxDB (time-series biometrics)
Streaming: HLS.js + WebRTC (video) + WebSocket (live biometrics)
Auth: Auth0
Payments: Razorpay (India) + Stripe (global)
```

### Coach Dashboard
```
Framework: React + D3.js (data visualization)
Charts: Recharts + custom heatmap
Real-time: WebSocket connection to edge server
Exports: PDF match report, CSV biometric data
```

---

## SAMPLE DEMO VIDEOS - FOOTBALL SCENARIO

### Video 1: The Goal (POV Recreation)
```
Scenario: Forward scores a goal in ISL
Simulation approach:
  1. Attach GoPro to foam mannequin at chest height
  2. Run the mannequin down a mock football field
  3. Record the "goal" moment
  4. Post-process: Add biometric overlay using After Effects
  5. 3DGS: Use NeRF/3DGS of the scene with 8 iPhone cameras
  6. Show before (normal TV broadcast) vs after (AthleteView)

Target duration: 60-second demo video
Distribution: Website hero section, YouTube, LinkedIn
```

### Video 2: The Kabaddi Raid
```
Simulation: HR timeline during a tense 8-second raid
Visualization: Real athlete wearing Apple Watch for real HR data
Post-process: Map the real HR to the kabaddi video overlay
Emotional hook: Show HR spike at the exact moment of escape
```

### Video 3: The 3DGS Moment
```
Record any fast sports moment with 8+ phones
Process with gsplat (open source)
Build the WebGL viewer
Show orbiting around a cricket shot or football header
Narration: "This is what AthleteView's free-viewpoint replay looks like"
```
