# 📋 AthleteView Pro - Full Product Specification

> **Version:** 1.0 | **Date:** March 2026 | **Author:** Pradhap (Founder)

---

## EXECUTIVE SUMMARY

AthleteView Pro is a two-tier wearable camera architecture per athlete:
- **1x Main Cam** (chest-mounted): Biometric hub + primary broadcast camera
- **2-4x Patch Cams** (shoulder/back/arm): Multi-angle video nodes

Every athlete becomes a self-contained broadcast unit. 22 players in football = 22 Main Cams + up to 88 Patch Cams = 110 live video feeds + 22 biometric data streams.

---

## TIER 1: MAIN CAM SPECIFICATION

### 1.1 Form Factor
| Parameter | Spec |
|-----------|------|
| Dimensions | 42mm x 34mm x 9.5mm |
| Weight | 18g (with battery) |
| Enclosure | IP67 rigid-flex PCB + medical-grade silicone overmold |
| Mounting | Integrated jersey pocket (chest center, sternum level) |
| Connector | Magnetic pogo-pin charging + data |

### 1.2 Camera & Video
| Component | Part | Spec |
|-----------|------|------|
| Image Sensor | **Sony IMX577** | 12MP, 1/2.3", BSI CMOS |
| SoC | **Rockchip RV1106** | Arm Cortex-A7 1.2GHz + RISC-V MCU + 0.5 TOPS NPU + ISP3.2 |
| Lens | M12, f/2.0 | 120° FOV, 4K-capable EFL |
| Video Encode | H.265/HEVC | 1080p@60fps (primary), 4K@30fps (standby) |
| Bitrate | 8–20 Mbps | Adaptive CBR/VBR based on scene complexity |
| HDR | WDR mode | 3-frame HDR, handles stadium lighting extremes |
| Low-light | ISP3.2 NR | Multi-level noise reduction, usable at 0.1 lux |
| Anti-shake | IMU-assisted EIS | 3-axis gyro stabilization via ICM42688 |
| Color Profile | P3 wide color | Log profile for post-processing |

### 1.3 Biometric Sensors
| Sensor | Part | Measurement | Accuracy |
|--------|------|-------------|----------|
| PPG (HR + SpO2) | **Analog Devices MAX86141** | Heart Rate 40–250 BPM, SpO2 70–100% | HR ±2 BPM, SpO2 ±2% |
| Skin Temperature | **Maxim MAX30208** | 32–42°C | ±0.1°C |
| 6-DOF IMU | **TDK ICM-42688-P** | Accel ±16g, Gyro ±2000 dps | 0.004 dps/√Hz |
| Sweat/Galvanic | **Custom GSR circuit** | Skin conductance 1–100 μS | ±5% |

**Why Chest for Biometrics?**
Chest placement achieves **7.7% median PPG error** vs 18.4% at wrist (validated in clinical studies). Closer to cardiac source = superior SNR for SpO2 and HR accuracy under motion.

### 1.4 Connectivity
| Interface | Technology | Spec |
|-----------|------------|------|
| Primary TX | **Qualcomm QCA6391 WiFi 6 + BT5.3** | 2.4/5GHz, WPA3, 1.8 Gbps peak |
| Backup TX | **5G Module (Quectel RM500Q)** | Sub-6GHz 5G NR, 2.1 Gbps DL |
| Patch Cam RX | BLE 5.3 Mesh | Receives compressed 2MP streams from Patch Cams |
| Streaming Protocol | **SRT (Secure Reliable Transport)** | 150-300ms latency, UDP, AES-128 |
| Time Sync | IEEE 1588 PTP | <1ms inter-camera sync across all feeds |

### 1.5 Power
| Parameter | Spec |
|-----------|------|
| Battery | 320 mAh LiPo (rechargeable, integrated) |
| Runtime | 90 min continuous 1080p60 streaming |
| Charging | 5V/1A USB-C via pogo pins, full charge in 45 min |
| Power Draw | 1.8W (streaming) / 0.4W (standby) |
| Battery Tech | SLPB553450H, 3.7V nominal |

### 1.6 Bill of Materials (Main Cam) - 1K Volume
| Component | Part Number | Unit Cost (INR) | Supplier |
|-----------|-------------|-----------------|----------|
| Rockchip RV1106 SoC | RV1106 (via Luckfox board) | ₹1,190 | Evelta India |
| Sony IMX577 module | 12MP MIPI CSI module | ₹4,200 | Mouser India / Alibaba |
| MAX86141 PPG sensor | MAX86141ENP+ | ₹530 | Mouser India |
| MAX30208 Temp | MAX30208BEWL+ | ₹380 | Mouser India |
| ICM-42688-P IMU | ICM-42688-P | ₹280 | Mouser India |
| QCA6391 WiFi6/BT | QCA6391 module | ₹1,800 | Aliexpress / Mouser |
| Quectel RM500Q 5G | RM500Q-GL | ₹7,500 | Quectel India |
| LiPo 320mAh | SLPB553450H | ₹420 | Battery supplier |
| Rigid-flex PCB | 4-layer RF | ₹1,200 | JLCPCB / PCBWay |
| Silicone enclosure | Medical IPX7 | ₹650 | Local mold manufacturer |
| Passive components | Caps, resistors, etc | ₹350 | LCSC / Mouser |
| **TOTAL BOM** | | **~₹18,500 (~$220)** | |

---

## TIER 2: PATCH CAM SPECIFICATION

### 2.1 Form Factor
| Parameter | Spec |
|-----------|------|
| Dimensions | 28mm x 22mm x 6mm |
| Weight | 7g |
| Enclosure | Flexible PCB + breathable sports adhesive |
| Mounting | Peel-and-stick on shoulder/back/sleeve (jersey integrated) |
| Connector | Wireless only (BLE 5.3 to Main Cam) |

### 2.2 Camera & Video
| Component | Part | Spec |
|-----------|------|------|
| Image Sensor | **Sony IMX307** | 2MP, 1/2.8" |
| SoC | **Rockchip RV1103** | Arm Cortex-A7 1.0GHz + NPU + ISP |
| Lens | Fixed, f/2.2 | 90° FOV |
| Video Encode | H.265 | 1080p@30fps, 4 Mbps |
| Compression | Hardware H.265 | Sends to Main Cam via BLE 5.3 |

### 2.3 Connectivity
| Interface | Technology | Purpose |
|-----------|------------|----------|
| TX to Main Cam | BLE 5.3 Mesh | Compressed video stream @ 4 Mbps |
| Sync trigger | GPIO via RF | Frame-accurate sync with Main Cam |

### 2.4 Power
| Parameter | Spec |
|-----------|------|
| Battery | 90 mAh LiPo |
| Runtime | 100 min |
| Charging | NFC/wireless charging via jersey pad |

### 2.5 Bill of Materials (Patch Cam) - 1K Volume
| Component | Part | Cost (INR) |
|-----------|------|------------|
| RV1103 SoC (Luckfox Pico) | Luckfox Pico Plus | ₹970 |
| Sony IMX307 module | 2MP MIPI CSI | ₹1,800 |
| Flex PCB | 2-layer | ₹550 |
| LiPo 90mAh | Custom | ₹180 |
| Adhesive medical patch | 3M 2477P | ₹90 |
| BLE antenna | Chip antenna | ₹60 |
| Passives | Various | ₹120 |
| **TOTAL BOM** | | **~₹3,770 (~$45)** |

---

## SYSTEM ECONOMICS PER ATHLETE

| Config | BOM Cost | Suggested Retail |
|--------|----------|------------------|
| Main Cam (1x) | ₹18,500 | ₹55,000 |
| Patch Cam (2x) | ₹7,540 | ₹18,000 |
| **Full athlete kit (1 Main + 2 Patch)** | **₹26,040** | **₹73,000** |
| Full football team (11 players) | ₹2.9 Lakh BOM | ₹8.0 Lakh |
| Gross Margin | ~65% | |

---

## PHYSICAL DESIGN LANGUAGE

### Design Principles
1. **Invisible to athlete** - feels like wearing nothing
2. **Aerodynamic** - tested in wind tunnel simulation, <0.3% drag increase
3. **Medical-grade materials** - no skin reactions for 90+ min wear
4. **Modular** - Jersey manufacturers integrate the pocket spec; patches are universal

### Material Stack (Main Cam)
```
Outer: Brushed polycarbonate lens bezel (scratch-resistant)
Middle: Medical-grade silicone body (IPX7, tear-proof)
Inner: Rigid-flex PCB (Rogers 4350B RF substrate)
Adhesive: 3M 9472LE medical adhesive (same as Dexcom CGM)
Base: Mesh-breathable spacer fabric backing
```

### Colors
- **Phantom Black** (default)
- **Arctic White** (light jerseys)
- **Custom team colors** (injection mold, MOQ 500 units)

---

## CERTIFICATIONS REQUIRED

| Cert | Body | Cost | Timeline |
|------|------|------|----------|
| BIS (India) | BIS India | ₹53,000 | 3-4 months |
| FCC (USA) | FCC | $8,000 | 4-6 months |
| CE (Europe) | TUV Rheinland | €6,500 | 3-5 months |
| IEC 60601 Medical | Intertek | $12,000 | 6 months |
| Bluetooth SIG | BT SIG | $5,000 | 1-2 months |
