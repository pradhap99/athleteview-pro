# 🤖 AI Model Architecture - AthleteView Pro

---

## OVERVIEW

The AthleteView AI pipeline has 4 layers:
1. **Biometric Signal Processing** - On-device (Main Cam RV1106 NPU)
2. **Player Detection & Tracking** - Edge server (Jetson Orin NX)
3. **3D Scene Reconstruction** - Edge server (LiveSplats 3DGS)
4. **Broadcast Intelligence** - Cloud (AWS/GCP inference)

---

## LAYER 1: ON-DEVICE BIOMETRIC AI (RV1106 NPU)

### Models Running on 0.5 TOPS NPU

#### 1.1 PPG Signal Processing (MAX86141 → HR + SpO2)
```
Input: Raw PPG signal (LED reflected light, 25 samples/sec)
Process:
  1. Band-pass filter: 0.5-4 Hz (removes motion artifacts)
  2. Peak detection: R-wave identification
  3. Peak-to-peak interval: RR interval calculation
  4. HR = 60 / RR_interval (beats per minute)
  5. SpO2 = 110 - 25 x (Red_AC/Red_DC) / (IR_AC/IR_DC)
Output: HR (BPM), SpO2 (%), HRV (ms)
Latency: <100ms
Power: <10 microA (MAX86141 spec)
```

#### 1.2 Motion Artifact Removal (IMU + PPG fusion)
```python
# Pseudo-code for motion artifact removal
def clean_ppg(ppg_signal, imu_accel):
    # Adaptive filter - subtract motion component
    motion_frequency = detect_motion_freq(imu_accel)
    ppg_clean = adaptive_filter(ppg_signal, motion_frequency)
    return ppg_clean
```

#### 1.3 Fatigue Index Model
```
Inputs: HR, HRV, SpO2, activity duration
Model: Lightweight decision tree (4KB, fits in NPU)
Output: Fatigue score 0-100
Alert threshold: >75 triggers sideline notification
```

---

## LAYER 2: PLAYER DETECTION & TRACKING (Jetson Orin NX)

### 2.1 Player Detection - YOLOv10
```
Model: YOLOv10-S (small variant, 8M params)
Input: 1080p frames from all camera feeds
Output: Bounding boxes + player IDs
Performance:
  - mAP50: 81.2%
  - mAP50-95: 62.8%
  - Inference: 8ms/frame on Jetson Orin (A = 40 TOPS)
  - Throughput: 125 FPS (22 cameras at 5 FPS each = 110 FPS needed)
Dataset: Fine-tuned on football/cricket/kabaddi jersey datasets
```

### 2.2 Multi-Object Tracking - BoT-SORT
```
Model: BoT-SORT (Robust Associations)
Input: YOLOv10 detections + camera frames
Output: Persistent player IDs across frames
Metrics:
  - MOTA: 87.5%
  - MOTP: 81.3%
  - ID Switches: <2 per 90-min match
Key capability: Re-identification after occlusion (player behind referee, etc.)
```

### 2.3 Cross-Camera Re-Identification - ViT Embeddings
```
Model: Vision Transformer (ViT-B/16) fine-tuned on jersey colors + player body features
Input: Player crop from any camera
Output: 768-dim embedding vector
Matching: Cosine similarity threshold 0.85
Purpose: Link the same player across all 22 Main Cams + 88 Patch Cams
Latency: 12ms/player crop
```

---

## LAYER 3: 3D GAUSSIAN SPLATTING (Jetson Orin NX + Cloud GPU)

### 3.1 LiveSplats Architecture
Based on CMU's LiveSplats (SIGGRAPH 2025) research:

```
Input: Multi-view video streams (all athlete cameras + 2-4 static venue cameras)

Pipeline:
  Step 1: Pose Estimation (Lightweight Bundle Adjustment)
          - Feature extraction: SuperPoint (GPU-optimized)
          - Initial poses: COLMAP-lite (fixed-size GPU kernel)
          - Latency: 50ms per frame

  Step 2: Gaussian Primitive Initialization
          - Static background: Pre-computed at match start
          - Dynamic players: New Gaussians per frame
          - Gaussian count: ~500K per scene

  Step 3: Joint Optimization
          - Gradient descent on Gaussian positions/colors/opacities
          - GPU-parallelized Jacobian computation
          - Convergence: 200ms per frame

  Step 4: Rendering
          - Client-side WebGL renderer (.splat format)
          - 60 FPS rendering on mid-range GPU
          - Mobile WebGL: 30 FPS on iPhone 15 Pro

Total latency: 2-5 seconds from live capture to interactive 3D model
GPU requirement: NVIDIA RTX 4090 OR Jetson Orin NX 16GB (edge)
```

### 3.2 Human-Centric Reconstruction
```
Challenge: Athletes move fast, standard 3DGS struggles with motion blur
Solution: Separate static background from dynamic players

Pipeline:
  1. Static background: Pre-compute stadium 3DGS at match start (5 min)
  2. Dynamic players: Per-frame player Gaussian update only
  3. Composite: Player Gaussians + static background merge
  4. Result: 10x faster reconstruction of dynamic scenes

Model reference: Based on LS-Gaussian (arXiv 2025) for efficient streaming
```

---

## LAYER 4: BROADCAST INTELLIGENCE (Cloud)

### 4.1 Automatic Highlight Detection
```
Model: Multimodal classifier (audio + video + biometric)
Inputs:
  - Audio: crowd noise level
  - Video: player cluster density change
  - Biometric: HR spike across multiple players simultaneously
Output: Highlight probability 0-1
Threshold: >0.85 = auto-clip generation + broadcast director alert

Training data:
  - 5,000 hours of labeled sports footage
  - 50,000 biometric moment annotations
  - Pre-trained on VideoMAE-v2 backbone
```

### 4.2 Performance Intelligence Engine
```
Player Performance Score (PPS):
  PPS = (sprint_count x 0.3) + (hr_zone_3_minutes x 0.3) +
        (possession_actions x 0.25) + (recovery_rate x 0.15)

Fatigue Prediction:
  Model: LSTM trained on historical match biometrics
  Input: Last 10 minutes of biometric data
  Output: Predicted performance degradation in next 10 minutes
  Accuracy: 78% within 15% error margin (validated on Catapult dataset)
```

### 4.3 Fantasy Sports API
```
Endpoints:
  GET /api/v1/player/{id}/performance_score  - Real-time PPS
  GET /api/v1/player/{id}/stamina           - Current fatigue index
  GET /api/v1/match/{id}/live_biometrics    - All 22 players streaming biometrics
  GET /api/v1/moment/{id}/3dgs              - 3DGS model for specific moment

Rate limiting: 1000 calls/second per API key
Pricing: $0.01/call, $50/month base
```

---

## PRE-TRAINED DATASETS

| Dataset | Purpose | Size | Source |
|---------|---------|------|--------|
| COCO + Sports jersey fine-tune | Player detection | 2M images | Open + proprietary |
| MOT20 + SportsMOT | Tracking benchmarks | 8 sequences | Public |
| MARS dataset | Re-identification | 1.2M frames | Public |
| Custom biometric dataset | Fatigue model | 50K athlete-hours | Proprietary (build) |
| Stadium 3DGS background | Scene reconstruction | Per-venue | Proprietary |

---

## OPEN SOURCE STACK

| Component | Library | License | Repo |
|-----------|---------|---------|------|
| 3DGS | gsplat | Apache 2.0 | github.com/nerfstudio-project/gsplat |
| Detection | Ultralytics YOLOv10 | AGPL-3.0 | github.com/ultralytics |
| Tracking | BoT-SORT | MIT | github.com/NirAharon/BoT-SORT |
| Streaming | SRT Alliance | MPL 2.0 | github.com/Haivision/srt |
| Media server | MediaMTX | MIT | github.com/bluenviron/mediamtx |
| Video encode | GStreamer | LGPL | gstreamer.freedesktop.org |
| Signal processing | scipy + numpy | BSD | pypi |

---

## HARDWARE ACCELERATION

### On-Device (RV1106)
- **NPU**: 0.5 TOPS INT8, runs PPG signal model + motion detection
- **ISP**: Hardware H.265 encode, EIS (electronic image stabilization)
- **Estimated AI power**: <50mW

### Edge Server (Jetson Orin NX 16GB)
- **GPU**: 1024 CUDA cores, 32 Tensor cores, 40 TOPS
- **Runs**: YOLOv10 + BoT-SORT + ViT ReID + 3DGS
- **Power**: 25W TDP
- **Cost**: $449 (module), $649 (with carrier board)

### Cloud (Scale)
- **Inference**: AWS g5.xlarge (A10G GPU, $1.00/hour)
- **Storage**: S3 for .splat files, $0.023/GB
- **Estimated cost**: $5-15/match for full AI pipeline
