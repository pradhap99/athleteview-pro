# AthleteView SmartPatch — Connectivity & Battery Technology Research Report
### Deep Dive: 2025–2026 Best-in-Class Components for 70×45×4mm Body-Worn Sports Wearable
**Prepared:** June 2025 | **Research Scope:** WiFi 6E/7, BLE 5.4+, 5G RedCap, UWB, Advanced Batteries, Waterproofing/PCB

---

## Executive Summary

The AthleteView SmartPatch (70×45×4mm) needs to stream 4K video and real-time biometric data from the body. This requires a radical rethink of the current module stack. The key findings:

1. **WiFi**: Infineon CYW55913 is the best single-chip solution (WiFi 6E + BLE 5.4 in 3.57×5.32mm), but cannot stream 4K alone with its 20MHz bandwidth cap. For 4K video streaming, a companion higher-throughput chip like the Nordic nRF7002 (86 Mbps max) may still be insufficient — true 4K needs 20–30+ Mbps sustained. The hybrid recommendation is CYW55913 + network edge compression.
2. **BLE**: Nordic nRF54L15 upgrades the nRF5340 with BLE 6.0, Channel Sounding, 50% lower RX power, and a tiny 2.4×2.2mm WLCSP package. Strongly recommended.
3. **5G/Cellular**: Quectel RG255C-GL (5G RedCap, 29×32×2.4mm LGA) is deployable in the patch and replaces the separate vest unit. At 223Mbps DL, it can serve as the primary video streaming pipe.
4. **UWB**: Qorvo QM35825 (new 2025 SoC, 4.08×3.38mm BGA, ±5cm accuracy, 3D AoA, ±2°) is the clear winner for player tracking.
5. **Battery**: Enovix silicon-anode cells (714–935 Wh/L) give 30–40% more capacity in the same form factor. NGK EnerCera (0.45mm semi-solid-state) is the most compelling for thin-patch designs. Standard LiPo remains the volume leader.
6. **PCB/Waterproofing**: ALD+Parylene C dual-stack coating delivers 100× WVTR improvement over Parylene alone. LCP substrates unlock RF performance above 5GHz for integrated antennas. Rigid-flex with LCP flex sections is the recommended PCB architecture.

---

## 1. WiFi Module Research

### 1.1 Current Baseline
| Parameter | RTL8852BE (Current) |
|-----------|---------------------|
| Standard | WiFi 6 (802.11ax) |
| MIMO | 2×2 |
| Max PHY Rate | ~1.8 Gbps (theoretical) |
| Price | ~$4.00/unit @ 10K |
| Use Case | Stable but no 6GHz; limited to 5GHz |

---

### 1.2 WiFi Candidate Comparison Table

| Chip | Standard | Max PHY Rate | Ch. BW | Package Size | BLE | Temp Range | Key Advantage | Wearable Fit |
|------|----------|-------------|--------|-------------|-----|------------|---------------|-------------|
| **Infineon CYW55913** | WiFi 6/6E | 143 Mbps (1×1, MCS11) | 20 MHz | **3.57×5.32mm WLBGA** | BLE 5.4 ✓ | -40–85°C | Smallest combo chip; integrated MCU (Cortex-M33); Matter; BLE+WiFi in one die | ★★★★★ |
| **Infineon ACW741x** | WiFi 7 (802.11be) | 86 Mbps (MCS7, 20MHz) | 20 MHz | **7×7mm QFN** | BLE 6.0 ✓ + 802.15.4 | -40–105°C | First IoT 20MHz WiFi 7; 70µW connected standby (15× lower than competing IoT chips); MLO; Channel Sounding | ★★★★☆ |
| **Nordic nRF7002** | WiFi 6 | 86 Mbps (MCS7) | 20 MHz | ~4×4mm SoC | No (companion IC) | -40–85°C | Designed as companion to nRF54L15/5340; ultra-low power design; paired with BLE SoC | ★★★☆☆ |
| **Qualcomm QCA6698AQ** | WiFi 6E | 2.4 Gbps (2×2, 160MHz) | 160 MHz | 7.42×6.85mm | BT 5.3 ✓ | Automotive grade | Highest throughput; automotive pedigree; 4K QAM; overkill for patch but most powerful | ★★☆☆☆ |
| **Realtek RTL8852CE** | WiFi 6E | 5.4 Gbps (AX5400) | 160 MHz | PCIe module | BT 5.3 ✓ | 0–55°C | High throughput; primarily laptop/desktop use; large PCIe form factor | ★☆☆☆☆ |
| **Realtek RTL8922AE** | WiFi 7 (802.11be) | 2.8 Gbps (2×2) | 160 MHz | M.2 2230 | BT 5.2 ✓ | 0–55°C | WiFi 7 MLO; high throughput; PCIe/USB form factor – too large for patch | ★☆☆☆☆ |
| **MediaTek MT7921** | WiFi 6 | ~1.8 Gbps | 80 MHz | PCIe | BT 5.2 ✓ | 0–55°C | Cost-effective dual-band; laptop chipset; not suitable for wearable | ★☆☆☆☆ |
| **ESP32-C6** | WiFi 6 | 150 Mbps | 20 MHz | QFN 7×7mm | BLE 5.0 ✓ | -40–85°C | Budget option ($1–2); good for prototyping; limited ecosystem for 4K video | ★★☆☆☆ |

**Sources:** [Infineon CYW55913 Product Page](https://www.infineon.com/part/CYW55913) | [Infineon ACW741x Launch](https://www.infineon.com/market-news/2026/infcss202601-039) | [CNX Software ACW741x](https://www.cnx-software.com/2026/01/26/infineon-airoc-acw741x-wi-fi-7-ultra-low-power-tri-radio-iot-soc-family-support-mlo-wi-fi-sensing-ble-6-0-and-thread/) | [All About Circuits CYW55913](https://www.allaboutcircuits.com/news/infineon-launches-wireless-mcu-featuring-wi-fi-6-6e-ble-matter/)

---

### 1.3 Infineon CYW55913 — Deep Dive (Top Pick for Patch)

**Architecture:** Single-chip MCU + WiFi 6/6E + BLE 5.4  
**Die Size:** 3.57 × 5.32 mm WLBGA (0.35mm pitch) — smallest tri-band combo on market  
**WiFi Specs:**
- Standard: 802.11ax (WiFi 6/6E), tri-band 2.4/5/6 GHz
- Spatial streams: 1×1 SISO
- Channel bandwidth: 20 MHz (not suitable for >100 Mbps throughput)
- Max PHY data rate: 143 Mbps (MCS11, 1024-QAM)
- TX power: up to +24 dBm (best-in-class range)
- RX sensitivity: -101.5 dBm
- Features: TWT (Target Wake Time), OFDMA, WPA3, Matter, HE ER-PPDU

**BLE Specs:**
- BLE 5.4, LE Long Range, LE Audio, isochronous channels
- TX power: +4/+13/+19 dBm (3 selectable output levels)
- RX sensitivity: -111.5 dBm (Long Range mode)

**MCU:** 192 MHz Arm Cortex-M33 + TrustZone (Security PSA L2)  
**Memory:** 768 KB SRAM, 2 MB ROM, QSPI external flash/PSRAM interface  
**Peripherals:** 12-bit 7-ch ADC, SDIO, SPI, UART, I2C, I2S, PDM, 47 GPIOs  
**Operating Temperature:** -40°C to +85°C  
**Modules Available:** USI WM-CYW-65U (8.6×8.1mm SIP with antenna), AzureWave AW-CU640 (16×25mm)  
**Price estimate:** ~$3.50–5.00/unit @ 10K (chip); ~$8–12/unit (module with antenna)

**⚠️ Critical Limitation:** 20 MHz bandwidth cap limits real throughput to ~80–100 Mbps sustained. 4K video at H.265 requires ~25–50 Mbps, which is achievable — but depends on clean 6GHz spectrum access. The chip eliminates the separate BLE chip entirely.

---

### 1.4 Infineon AIROC ACW741x — WiFi 7 IoT (2026 Newcomer)

**Architecture:** Tri-radio SoC: WiFi 7 + BLE 6.0 + 802.15.4 (Thread/Matter)  
**Package:** 7×7mm QFN-60 (larger than CYW55913 but more capable)  
**WiFi 7 Key Differentiators:**
- 20 MHz-only 1×1 WiFi 7 (first-in-class for IoT)
- MLO (Multi-Link Operation) across 2.4/5/6 GHz simultaneously → resilient streaming
- Wi-Fi sensing (IEEE 802.11bf, CSI-based)
- **Connected standby power: 70 µW** (15× lower than competing IoT WiFi chips)
- TX power: up to +23 dBm; RX sensitivity: -100 dBm

**BLE 6.0 with Channel Sounding:** High-accuracy ranging built in — eliminates need for separate UWB in some use cases  
**Power Consumption:** 70 µW connected standby; 3× improvement in active TX vs competitors  
**Temperature:** -40°C to +105°C (industrial)  
**Availability:** Sampling 2026  
**Price estimate:** ~$5–7/unit @ 10K (projected, not yet commercially priced)

**Assessment:** Better long-term choice than CYW55913 due to WiFi 7 MLO robustness and BLE 6.0. Recommended for v2 hardware (2026+ target).

---

### 1.5 Key Insight on 4K Video Streaming via WiFi

4K video at 30fps compressed with H.265 requires **15–25 Mbps** sustained bandwidth. H.264 requires **25–50 Mbps**. The 20MHz WiFi 6E channel in CYW55913 can deliver **~80–100 Mbps real throughput** in ideal conditions, making 4K *technically* feasible — but:
- Requires clean 6GHz spectrum (stadiums may have interference)
- Latency sensitive (live sports requires <100ms end-to-end)
- **Recommended approach:** Use 5G RedCap as primary 4K video pipe; WiFi as secondary/local streaming

---

## 2. BLE Module Research

### 2.1 Current Baseline
| Parameter | nRF5340 (Current) |
|-----------|-------------------|
| BLE | 5.3 |
| Core | Dual Cortex-M33 |
| RX Current | ~4.6 mA |
| Package | 7×7mm aQFN |
| Price | ~$4.00/unit @ 10K |

---

### 2.2 BLE Candidate Comparison Table

| Chip | BLE Ver. | Channel Sounding | RX Current | Sleep Current | Package | Temp | Est. Price | Verdict |
|------|----------|-----------------|------------|--------------|---------|------|------------|---------|
| **Nordic nRF54L15** | **6.0** | ✓ Yes | ~3.2 mA | **0.8 µA** | **2.4×2.2mm WLCSP** | -40–105°C | ~$3.50 | ★★★★★ Best overall |
| **Nordic nRF54H20** | 6.0 | ✓ Yes | **1.7 mA** | <2 µA | 9×9mm VQFN (est.) | -40–85°C | ~$5–7 | ★★★★☆ Premium pick |
| **Infineon CYW55913** | 5.4 | No | ~4–5 mA | ~10–50 µA | 3.57×5.32mm WLBGA | -40–85°C | ~$3.50 | ★★★★☆ Best if replacing WiFi+BLE |
| **Infineon ACW741x** | **6.0** | ✓ Yes | ~3–4 mA | <70 µW (WiFi) | 7×7mm QFN | -40–105°C | ~$5–7 | ★★★☆☆ Good if using WiFi 7 too |
| **Silicon Labs EFR32BG27** | 5.4 | No | 3.6 mA | **1.6 µA** | Ultra-small SiP options | -40–125°C | ~$2–3 | ★★★☆☆ Budget/compact |
| **TI CC2340R5** | 5.3 | No | 5.3 mA | 0.7 µA | Small QFN | -40–125°C | **$0.79** | ★★☆☆☆ Ultra-cheap but not BLE 6.0 |
| **Nordic nRF5340** (current) | 5.3 | No | 4.6 mA | 1.5 µA | 7×7mm | -40–85°C | ~$4.00 | — Baseline |

**Sources:** [Nordic nRF54L15 Product Page](https://www.nordicsemi.com/Products/nRF54L15) | [Nordic nRF54H20 Page](https://www.nordicsemi.com/Products/nRF54H20) | [Silicon Labs EFR32BG27](https://www.silabs.com/wireless/bluetooth/efr32bg27-series-2-socs) | [TI CC2340 Launch](https://www.allaboutcircuits.com/news/ti-rolls-out-bluetooth-le-mcu-with-8-dbm-rf-power-for-0.79/)

---

### 2.3 Nordic nRF54L15 — Deep Dive (Top BLE Pick)

**Why it beats nRF5340:**
- **BLE 6.0** including **Channel Sounding** (high-accuracy ranging, ±10cm possible at close range — can complement or partially replace UWB)
- **RX current: 3.2 mA** (vs 4.6 mA nRF52840, vs 2.7 mA nRF5340 — note nRF54L15 improves on nRF52 but nRF5340 is already 2.7mA; nRF54H20 at 1.7mA is still lower)
- **Sleep current: 0.8 µA** with Global RTC running (vs 1.5 µA on nRF52840)
- **Package:** 2.4×2.2mm WLCSP — dramatically smaller than nRF5340's 7×7mm
- **CPU:** 128 MHz Cortex-M33 + 128 MHz RISC-V coprocessor (2× performance vs nRF52840)
- **Memory:** 1.5 MB NVM (RRAM), 256 KB RAM
- **Protocols:** BLE 6.0, Thread, Zigbee, Matter, Amazon Sidewalk, proprietary 4 Mbps
- **Security:** PSA Certified Level 3 (TrustZone, side-channel protection, tamper detection)
- **ADC:** 14-bit, 8-channel (useful for biometric sensors)
- **Temperature:** -40°C to +105°C
- **WiFi companion:** Can pair with nRF7002 for WiFi 6 using nRF Connect SDK

**Channel Sounding (Key Feature for AthleteView):**  
BLE Channel Sounding (introduced in BLE 6.0/Core Spec 6.0) provides ranging via phase-based and RTT-based distance measurements. Accuracy: **±10 cm** at <10m range in good conditions. While not matching UWB's ±5cm or 3D AoA, it reduces the need for a separate UWB chip in lower-cost configurations.

---

### 2.4 Nordic nRF54H20 — Premium High-Performance Pick

**Best for:** Applications needing ML/AI at the edge, ultra-low RX power  
- **RX current: 1.7 mA** (lowest BLE RX power available — critical for always-on biometric streaming)
- **BLE 6.0**, first chip to break -100 dBm sensitivity for 1 Mbps BLE LE
- **Cores:** Multiple Cortex-M33 (up to 320 MHz app core) + RISC-V coprocessors
- **Memory:** 2 MB NVM + 1 MB SRAM (enables on-device ML models)
- **Security:** PSA Level 3 IoT
- **Applications listed by Nordic:** Gaming, advanced wearables, VR/AR, medical
- **Status:** Available for sampling 2024; production 2025

**Cost delta:** ~$3–4 premium over nRF54L15. Worth it if the patch runs on-device sensor fusion or ML inference.

---

### 2.5 Strategic BLE Decision: Consolidate Chips

**Option A (Recommended):** nRF54L15 (BLE 6.0) + CYW55913 (WiFi 6E/BLE 5.4)  
→ Use CYW55913 as primary WiFi path; nRF54L15 handles BLE 6.0/Channel Sounding/sensor fusion  
→ Both chips can coexist via 2-wire/3-wire coexistence interface  
→ Total die area: ~(3.57×5.32) + (2.4×2.2) = ~24mm²

**Option B (Aggressive Consolidation):** CYW55913 alone handles both WiFi and BLE  
→ Eliminates one chip; BLE is 5.4 (not 6.0); no Channel Sounding  
→ Reduces BOM by $3–4/unit

**Option C (Premium):** Infineon ACW741x (WiFi 7 + BLE 6.0 + Thread) alone  
→ Single chip handles everything; BLE 6.0 with Channel Sounding  
→ Larger footprint (7×7mm); available 2026

---

## 3. 5G/Cellular Module Research

### 3.1 Current Baseline
| Parameter | Quectel RM500Q (Current) |
|-----------|--------------------------|
| Technology | 5G NR Sub-6 (full 5G) |
| Form Factor | Separate vest unit (M.2) |
| Peak DL | 4 Gbps |
| Power | High (3–4W active) |
| Size | 52×30×2.3mm |

**Problem:** Full 5G modules are too large, too power-hungry, and too expensive for patch integration.

---

### 3.2 5G RedCap — Why It Changes Everything

5G RedCap (3GPP Release 17 Reduced Capability NR) was specifically designed to bridge the gap between LTE-M and full 5G for wearables and IoT. Key reductions vs full 5G:
- 1×1 or 2×2 MIMO vs 4×4+
- 20 MHz max bandwidth vs 100+ MHz
- ~65% simpler silicon → **50% lower module cost**, **50% lower power**
- Peak DL: 150–223 Mbps — sufficient for 4K H.265 streaming
- Supports 5G SA features: network slicing, URLLC, ultra-low latency

[Source: 5G RedCap IoT Guide 2025](https://spenza.com/telecom/what-is-5g-redcap-iot-iiot-guide-2025/)

---

### 3.3 5G RedCap Module Comparison Table

| Module | Standard | DL / UL | Size (mm) | Power | Temp | Chipset | Form Factor | Est. Price | Fit |
|--------|----------|---------|-----------|-------|------|---------|-------------|------------|-----|
| **Quectel RG255C-GL** | 5G RedCap R17 | 223 / 123 Mbps | **29×32×2.4** | 2.5mA sleep / 25mA idle | -30–75°C (-40–85 ext) | Snapdragon X35 | LGA | ~$40–60 | ★★★★★ |
| **Fibocom FG132 (LGA)** | 5G RedCap R17 | 223 / 123 Mbps | **29×32×2.4** | Not published | -35–75°C (-40–85 ext) | — | LGA | ~$140 retail | ★★★☆☆ |
| **Fibocom FG132 (M.2)** | 5G RedCap R17 | 226 / 121 Mbps | 30×52×3.1 | Not published | -35–75°C | — | M.2 | — | ★★☆☆☆ |
| **Sierra Wireless RC7620** | LTE Cat-6 | 300 / 50 Mbps | 28.8×28.8×2.2 | ~5mA sleep | -40–85°C | — | LGA | ~$30–50 | ★★☆☆☆ (LTE only) |
| **Nordic nRF9161** | LTE-M / NB-IoT | 10.3 / 2.2 Mbps | 10×16mm SiP | <0.5 µA | -40–85°C | Integrated | LGA SiP | ~$8–12 | ★☆☆☆☆ (no 5G) |

**Sources:** [Quectel RG255C Specs](https://www.quectel.com/product/5g-redcap-rg255c-series/) | [Fibocom FG132 Datasheet](https://www.m2mgermany.de/shop/media/webshop_dl/Fibocom/8071_Fibocom_FG132_Datasheet_V1.3.pdf) | [Quectel RG255C DigiKey](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/8893/Quectel_RG255C.pdf)

---

### 3.4 Quectel RG255C-GL — Deep Dive (Top 5G Pick)

**Form Factor:** 29×32×2.4mm LGA — fits **within the 70×45mm patch footprint** (occupies ~35% of patch area)  
**Baseband:** Qualcomm Snapdragon X35 (world's first 5G RedCap modem)  
**Standards:** 3GPP Release 17 RedCap; supports 5G SA mode; backward compatible with LTE Cat-4, R15, R16  
**Data Rates:** 223 Mbps DL / 123 Mbps UL (5G RedCap); 195 Mbps DL / 105 Mbps UL (LTE)  
**Power Consumption:**
- Sleep: 2.5 mA
- Idle: 25 mA
- Active TX: ~500–800 mA (peak)
**Supply Voltage:** 3.3–4.3V, typical 3.8V  
**Operating Temperature:** -30°C to +75°C standard; -40°C to +85°C extended  
**Interfaces:** USB 2.0, PCIe 2.0 (for WiFi/BT offload), UART, SGMII, SPI  
**GNSS:** Optional multi-constellation (GPS, GLONASS, BeiDou, Galileo, QZSS)  
**Features:** 5G LAN, URLLC, network slicing, VoNR optional  
**Regional Variants:** CN, GL, NA, EU

**Critical Note on Power:** Active TX at 500–800 mA peak is the biggest challenge. The 800mAh patch battery would be heavily depleted during continuous 5G streaming. Duty-cycling 5G transmission (buffering + burst) is required.

**Recommendation:** RG255C-GL is the right module for patch-integrated 5G. Size is achievable; power management is the key engineering challenge.

---

## 4. UWB (Ultra-Wideband) Research

### 4.1 Why UWB Matters for AthleteView

UWB provides centimeter-level position tracking with <1ms latency — essential for:
- Real-time player position on field (cm accuracy vs GPS's ~1–3m)
- Collision detection / proximity alerts
- Play reconstruction analytics
- The NFL has deployed UWB (via Zebra Technologies) since 2014 with 20–30 anchors per stadium, tracking >1,000 data points/second

[Source: FiRa Consortium — UWB in Sports](https://www.firaconsortium.org/resource-hub/blog/how-ultrawideband-is-tackling-sports)

---

### 4.2 UWB Chip Comparison Table

| Chip | Ranging Accuracy | AoA | 3D AoA | Data Rate | Package | Frequency | Price | Fitness |
|------|-----------------|-----|--------|-----------|---------|-----------|-------|---------|
| **Qorvo QM35825** (2025) | **±5 cm** | ✓ | ✓ 3D | 62.4 Mbps | **4.08×3.38mm BGA-74** | 6.5 & 8 GHz | TBD | ★★★★★ |
| **Qorvo DW3220** | <10 cm | ✓ PDoA | ✓ | 6.8 Mbps | 5×5mm QFN | 6.5 & 8 GHz | ~$15–20 | ★★★★☆ |
| **NXP Trimension SR150** | High precision | ✓ AoA | ✓ 3D | High perf. | WLCSP68 | 802.15.4z | **$3.96** @ 1K | ★★★★☆ |
| **NXP Trimension SR040** | High precision | No | No | Reliable | Small | 802.15.4z | ~$10 | ★★★☆☆ |
| **Qorvo DWM3000** (module) | 10 cm | No | No | 6.8 Mbps | Module | 6.5 & 8 GHz | $17–24 | ★★★☆☆ |

**Sources:** [Qorvo DW3220 Product Page](https://www.qorvo.com/products/p/DW3220) | [Qorvo QM35825](https://www.qorvo.com/products/p/QM35825) | [NXP Trimension SR150](https://www.nxp.com/products/SR150) | [Nextwaves UWB Comparison](https://nextwaves.com/blog/the-ultimate-uwb-module-comparison-prices-specs-and-use-cases)

---

### 4.3 Qorvo QM35825 — Deep Dive (New 2025 UWB SoC)

**The most significant UWB release of 2025 — specifically designed for sports/industrial tracking**

**Specs:**
- Frequency: 6.5 GHz (Ch. 5) and 8 GHz (Ch. 9)
- Ranging accuracy: **±5 cm** (exceeds DW3220's <10 cm)
- AoA accuracy: **±2°** (3D Angle of Arrival)
- Link budget: **104 dB** — longest range in class
- Data rates: 850 kbps, 6.8 Mbps, 7.8 Mbps, 27.2 Mbps, 31.2 Mbps, **62.4 Mbps** (proprietary)
- Package: **4.08×3.38×0.63mm BGA-74** — smallest footprint UWB SoC
- Supply: 1.14–3.6V
- Antenna ports: 4 flexible RF ports with LNAs, PA, RF switches
- On-chip: Cortex-M33 + Secure Enclave; ML/AI ranging algorithms
- Standards: IEEE 802.15.4-2024; FiRa 3.0 certified; FiRa, Aliro, Omlox ranging
- Security: SESIP3 compliant; STS secure ranging; AES; Secure Boot

**Key differentiators vs DW3220/DW3220:**
- Fully integrated SoC (no external MCU needed)
- On-chip AI/ML for ranging enhancement
- 4 antenna ports (vs 2 on DW3220) — enables proper 3D triangulation from wrist/back position
- 104 dB link budget (up from ~94 dB on DW3000) → 50%+ longer range
- ±5 cm vs <10 cm accuracy improvement
- Proprietary 62.4 Mbps mode for data-intensive applications

**Sources:** [Qorvo QM35825 Spec](https://www.qorvo.com/products/p/QM35825) | [Qorvo RFMW Listing](https://www.rfmw.com/products/detail/qm35825-qorvo/857731/) | [Qorvo Press Release 2025](https://www.qorvo.com/newsroom/news/2025/qorvo-expands-ultra-wideband-portfolio-with-first-fully-integrated-low-power-soc)

---

### 4.4 NXP Trimension SR150 — Infrastructure Anchor Option

The SR150 at **$3.96/unit** (1K volumes) is the most cost-effective option for deploying many **stadium anchor nodes** (not necessarily for the player patch itself). The SR150 provides:
- FiRa certified (industry interoperability)
- Apple U1/U2 interoperability (firmware 3.14.0)
- 3D AoA via dual RX
- Embedded secure element via EdgeLock SE051W

**Recommended Architecture:** Use QM35825 in the player patch (for its compact BGA and integrated MCU), and SR150 in fixed stadium infrastructure anchors (for cost efficiency at scale).

---

### 4.5 UWB in Sports — Performance Reality Check

Academic study of UWB in tennis (2025) found ([Sensors journal, 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11859737/)):
- ICC of 0.913 (excellent reliability for steady movements)
- Average positioning error: 11.3 cm (fused with IMU) vs 14.2 cm (standalone)
- **Key limitation:** Accuracy degrades during high-intensity direction changes (common in all sports)
- **Solution:** Fuse UWB with IMU (existing in the AthleteView patch) for optimal accuracy

This confirms UWB + IMU fusion as the correct architecture. The QM35825's on-chip ML capabilities are designed exactly for this.

---

## 5. Battery Technology Research

### 5.1 Current Baseline
| Parameter | Standard LiPo (Current) |
|-----------|-------------------------|
| Capacity | 800 mAh |
| Energy Density | ~600–650 Wh/L (typical LiPo) |
| Gravimetric | ~200–250 Wh/kg |
| Price | ~$1.80/unit @ 10K |
| Charge Rate | 0.5–1C typical |
| Swelling | Yes |
| Temperature | -20 to +60°C |

---

### 5.2 Battery Technology Comparison Table

| Technology | Energy Density (Vol.) | Energy Density (Grav.) | Charge Rate | Cycle Life | Flexibility | Safety | TRL | Est. Cost | Verdict |
|------------|----------------------|----------------------|-------------|------------|-------------|--------|-----|-----------|---------|
| **Standard LiPo** | 600–650 Wh/L | 200–250 Wh/kg | 0.5–1C (1–2hr) | 300–500 | No | Moderate | 9 | $1.80 | Baseline |
| **Enovix Silicon-Anode** | **714–935 Wh/L** | 258+ Wh/kg | 3C (20min to 50%) | 500–900 | No | Good | 8 | ~$4–8 | ★★★★★ |
| **Sila Nano (Titan Silicon)** | ~720 Wh/L (+17–40%) | ~350 Wh/kg | 15min 10-80% | 800+ | No | Good | 8 | ~$3–6 | ★★★★☆ |
| **NGK EnerCera Pouch** | N/A (ultra-thin) | — | ~14 min to 80% | High | **Yes (0.45mm)** | **Excellent** | 7 | Higher | ★★★★★ (thin patches) |
| **Jenax J.Flex** | Similar to LiPo | ~200 Wh/kg | Standard | 10,000 flex cycles | **Yes (2mm bend radius)** | Good | 7–8 | ~3–5× LiPo | ★★★☆☆ |
| **Ilika Stereax** | High (miniature) | — | Fast charge capable | 1000s | No | **Excellent (solid-state)** | 6–7 | Very high | ★★★☆☆ (medtech focus) |
| **ProLogium LCB (Gen 4)** | 860–900 Wh/L | 380 Wh/kg | 4 min to 60% | — | No | **Excellent** | 6 (EV-scale) | Very high | ★★☆☆☆ (EV focus) |
| **Graphene-enhanced LiPo** | ~700 Wh/L | ~260 Wh/kg | 22–27% faster than LiPo | Long | No | Good | 7 | ~2× LiPo | ★★★☆☆ |
| **BrightVolt (solid-state PME)** | Custom thin-film | Low-capacity | Standard | Standard | **Yes** | Excellent | 7 | Specialized | ★★☆☆☆ |

**Sources:** [Enovix AI-1 Independent Testing](https://ir.enovix.com/news-releases/news-release-details/independent-testing-confirms-enovix-ai-1tm-achieves-935-whl/) | [Enovix Wearable Data Sheet](https://www.enovix.com/wp-content/uploads/2023/01/602d3e2d1b41897a1bb7c1c1_Enovix-Wearable-Cell-Data-Sheets.pdf) | [NGK EnerCera Wearables](https://wearable-technologies.com/news/august-2025-ultra-thin-battery-revolution-in-wearables) | [ProLogium CES 2025](https://prologium.com/prologium-shines-bright-at-ces-2025-with-fully-inorganic-electrolyte-battery-breakthroughs/) | [Sila Nano Whoop 4.0](https://www.siliconrepublic.com/machines/sila-battery-energy-density-wearables)

---

### 5.3 Enovix Silicon-Anode Battery — Deep Dive (Top Pick for Volume Production)

**Why it's the #1 wearable battery choice for 2025:**

**Architecture:** 3D cell design with constrained silicon anode prevents the ~300% silicon swelling problem that kills silicon-anode batteries from other vendors. 100% silicon anode, no graphite.

**Wearable Cell Specs (from Enovix datasheet):**
- Capacity: 340 mAh (wearable cell reference)
- Energy: 1.24 Wh
- Volumetric energy density: **714 Wh/L** (baseline wearable cell, 2023)
- Gravimetric energy density: 258 Wh/kg
- Voltage: 3.63V avg discharge, 4.35V max / 2.70V min
- Cycle life: 500 cycles to 80% at 25°C; 500 cycles to 60% at 45°C
- Cell mass: 4.79g
- Dimensions: ~17.3×28.9×2.0mm (reference cell)
- Charge rate: 0.7C CC-CV (standard); 3C fast charge (AI-1 platform)

**AI-1 Platform (2025 — Smartphone grade, applicable to wearable):**
- Volumetric density: **935 Wh/L** (independently verified by Polaris Battery Labs, Jan 2026)
- Fast charge: **3.8 minutes to 20%**, 12.3 minutes to 50%, 39.5 minutes to full (at 3C)
- Cycle life: 900+ cycles (initial smartphone testing)
- Wearable AI-1 target: **>1,000 Wh/L** (stated by CEO for wearable format)

**Impact on AthleteView:**  
Current 800mAh LiPo @ ~600 Wh/L → Enovix silicon-anode @ 714–935 Wh/L in same physical volume = **1,050–1,240 mAh** in same cell footprint (~30–55% more capacity).

Or maintain 800mAh and reduce battery volume by 30–40% — freeing space for electronics.

[Sources: Enovix IR](https://ir.enovix.com/news-releases/news-release-details/independent-testing-confirms-enovix-ai-1tm-achieves-935-whl/) | [Enovix AI-1 Launch](https://www.globenewswire.com/news-release/2025/07/07/3111025/0/en/Enovix-Launches-AI-1-A-Revolutionary-Silicon-Anode-Smartphone-Battery-Platform.html)

---

### 5.4 NGK EnerCera — Breakthrough for Ultra-Thin Patches

**The most compelling technology for a 4mm-thick body-worn patch:**

| EnerCera Parameter | Value |
|--------------------|-------|
| Thickness | **0.45mm** |
| Weight | <1g |
| Technology | Semi-solid-state (crystal-oriented ceramic electrodes) |
| Swelling | **None** — ceramic electrodes cannot swell |
| Fire risk | **None** — non-flammable |
| Flexibility | 10,000+ bend cycles at 0.45mm |
| Nominal voltage | 3.8V (high-capacity) / 2.3V (fast-charge) |
| Reference capacity | 15–27 mAh (38×27mm footprint) |
| Fast charge models | 0–80% in **14 minutes** |
| Heatproof | 80–135°C variants |
| Integration | Hot-lamination compatible (embedded in substrate) |

**Critical Limitation:** Capacity is very low per unit (15–27 mAh per cell). For 800mAh total, you would need ~30–50 stacked or tiled EnerCera cells — complex but **architecturally possible** with a tiled patch design. Alternatively: use EnerCera for a backup/always-on power layer + Enovix main cell.

[Source: NGK EnerCera Product Page](https://wearable-technologies.com/news/august-2025-ultra-thin-battery-revolution-in-wearables) | [NGK EnerCera Evaluation Board](https://ipxchange.tech/evaluation-boards/ngk-enercera-pouch-bendable-li-ion-rechargeable-battery-evaluation-board/)

---

### 5.5 Sila Nano Titan Silicon — Wearable Commercial Deployment

**Already deployed commercially in Whoop 4.0 fitness tracker (2021):**
- Energy density: +17% vs graphite baseline in Whoop deployment
- Future potential: +40% improvement stated
- Moses Lake plant (WA): Commercial wearable shipments starting Q3 2025
- Cycle life: 800+ cycles (80% retention); SEI stabilization proprietary
- Fast charge: 15 minutes for 10–80% SOC
- Safety: Patented 3D porous structure limits expansion to 80–100% (vs 300% in pure silicon)

**Assessment:** More conservative/proven than Enovix; excellent supply chain reliability for mass production. Enovix AI-1 has higher peak density; Sila has broader wearable OEM relationships.

---

### 5.6 Battery Recommendations by Priority

| Priority | Recommendation | Why |
|----------|---------------|-----|
| **#1 Near-term (2025)** | Enovix silicon-anode wearable cell | +30–55% capacity gain in same volume; commercially available; fast charge |
| **#2 Near-term (2025)** | Sila Nano Titan Silicon LiPo | Proven in wearables; Q3 2025 commercial supply; +17–40% density |
| **#3 Mid-term (2026)** | NGK EnerCera tiled array | Ultra-thin (0.45mm), no swelling/fire, hot-lamination compatible |
| **#4 Future (2027+)** | ProLogium/QuantumScape miniaturized solid-state | >900 Wh/L solid-state; no current wearable format available |

---

### 5.7 Fast Charging for Sports Context

Sports use demands rapid turnaround between sessions. Targets:
- **15 minutes:** Enovix AI-1 at 3C → 50% charged (achievable now)
- **30 minutes:** Full charge feasible with 2C–3C if thermal management allows
- **Temperature:** Enovix rated -20°C to +60°C (adequate for outdoor sports); solid-state options perform better at extremes

---

## 6. Waterproofing & PCB Advanced Technology

### 6.1 Conformal Coating Comparison

| Technology | Thickness | WVTR Improvement | IP Rating Achievable | Cost | Temp Range | Sports Wearable Fit |
|------------|-----------|-----------------|---------------------|------|------------|---------------------|
| **Standard Parylene C** | 5–25 µm | Baseline | IP57–IP58 | Medium | -200–125°C | ★★★☆☆ |
| **ALD (Al₂O₃ 10nm) + Parylene C** | 10nm + 15µm | **100× better WVTR** | IP68+ | Higher | Same as Parylene | ★★★★★ |
| **P2i Nano-coating (Barrier Max)** | ~30nm | Molecular-level | Up to IPX8 device-level | Low-medium | -40–125°C | ★★★★☆ |
| **Liquipel (plasma-activated)** | ~30nm | Good | IPX4–IPX6 | Low | — | ★★★☆☆ |
| **Semblant FluroTech** | ~50nm | Good | IPX4–IPX6 | Low | — | ★★★☆☆ |

**Sources:** [ALD-Parylene IMAPS Study](https://imapsource.org/article/129018-atomic-layer-deposition-parylene-conformal-nanocoatings-for-robust-corrosion-protection-of-electronics.pdf) | [P2i Waterproofing](https://www.p2i.com/2016/10/13/maximising-water-proof-electronics-with-advanced-conformal-coatings/) | [Forge Nano ALD for RF](https://www.forgenano.com/archivesite/atomic-layer-deposition-for-rf-devices/)

---

### 6.2 ALD + Parylene C — Recommended Dual-Stack Approach

**Why ALD first, then Parylene:**
- ALD deposits ultra-thin Al₂O₃ (10–100nm) with **zero pinholes** — pinholes in conventional coatings are the primary water ingress point
- ALD alone is brittle; Parylene over ALD provides mechanical strength
- Combined WVTR: **<5×10⁻¹⁶ g/cm²/s** (essentially hermetic at 15µm Parylene over 10nm ALD)
- Can coat complex 3D assemblies including beneath IC leads
- ALD process temperature: as low as 70°C — safe for all components
- Added mass: negligible (100nm ALD = negligible; 15µm Parylene = ~0.1g/patch)
- Process: High-volume capable (batch ALD, CVD Parylene)

**P2i as Alternative:** P2i's "Barrier Max" variant achieves IPX8 device-level protection and is already deployed on Samsung Galaxy products. Nano-scale plasma deposition is faster/cheaper than ALD-Parylene but provides less extreme barrier performance. Suitable if ALD capex is not justified.

---

### 6.3 PCB Architecture Options

#### Current: 6-Layer Rigid PCB

#### Option A: Rigid-Flex with LCP Flex Sections
**Liquid Crystal Polymer (LCP) substrate for flex zones:**
- Dielectric constant: 2.9–3.5 (stable from DC to 110 GHz)
- Moisture absorption: <0.04% (near-hermetic)
- CTE: 10–17 ppm/°C (excellent thermal stability)
- Thickness: as thin as 25 µm
- Key advantage: **LCP enables antenna integration at 5GHz, 6GHz, 7.9GHz bands** — all relevant to WiFi 6E, WiFi 7, and UWB bands
- Used in 5G mmWave antennas in Apple iPhones

**Recommended stack:**
- Rigid sections: FR4 or Rogers RO4003C for RF components
- Flex sections: LCP for antenna runs, fold-across-body interconnects
- ALD-Parylene over entire assembled board
- 8-layer (upgrade from 6-layer) to enable signal/power isolation for 5G + WiFi + UWB simultaneous operation

[Source: LCP for Wearables](https://www.samaterials.com/content/lcp-film-enabling-5g-wearables-and-aerospace-advances.html) | [Microwave Journal LCP](https://www.microwavejournal.com/articles/6219-liquid-crystal-polymer-enabling-next-generation-conformal-and-multilayer-electronics)

---

#### Option B: MID (Molded Interconnect Device) — 3D PCB

**For housing/antenna integration:**
- Laser Direct Structuring (LDS) deposits conductive traces directly on 3D plastic housing
- Antennas printed into the housing → eliminates dedicated PCB antenna area
- Reduces component count; integrates antenna into mechanical structure
- Market growing to $18.56B by 2027; strong adoption in wearables and 5G modules
- Compatible with WiFi 6E, BLE, UWB antenna integration

**Assessment:** MID is ideal for the patch housing/enclosure layer, freeing interior PCB space for electronics. Use MID for WiFi 6E and BLE antennas; keep UWB on dedicated PCB due to precision timing requirements.

[Sources: MID Market Overview](https://www.businesswebwire.com/molded-interconnect-device-market/) | [MID Smart Devices](https://www.precedenceresearch.com/insights/molded-interconnect-devices-next-gen-smart-devices)

---

### 6.4 PCB Thickness Reduction Path

| PCB Type | Typical Thickness | Notes |
|----------|------------------|-------|
| Current 6-layer rigid | 1.2–1.6mm | Standard FR4 |
| 6-layer rigid-flex | 0.8–1.0mm | Flex zones at 0.1mm |
| 6-layer LCP rigid-flex | 0.6–0.8mm | LCP flex sections at 25–75µm |
| 8-layer LCP rigid-flex | 0.9–1.1mm | Required for 5G+WiFi+UWB isolation |
| MID + embedded PCB | 0.5–0.8mm total | For aggressive miniaturization |

In a 4mm-thick patch with housing (0.5mm top + 0.5mm bottom), battery (1.5–2mm), and PCB + components (~1mm), there is minimal margin. Target: **8-layer LCP rigid-flex at 0.8–1.0mm** with low-profile BGA components.

---

## 7. Recommended Module Stack — AthleteView v2

### 7.1 Recommended Bill of Materials vs Current

| Function | Current | Recommended v2 | Change |
|----------|---------|----------------|--------|
| WiFi | RTL8852BE (WiFi 6, $4.00) | **Infineon CYW55913** (WiFi 6E tri-band, ~$4.50) | +$0.50; eliminates BLE chip; adds 6GHz |
| BLE | nRF5340 ($4.00) | **Nordic nRF54L15** (BLE 6.0, 2.4×2.2mm, ~$3.50) | -$0.50; BLE 6.0; Channel Sounding; 50% lower RX power |
| 5G/Cellular | Quectel RM500Q (vest unit) | **Quectel RG255C-GL** (5G RedCap, 29×32mm, ~$45 est.) | Integrated into patch; 50% lower power vs full 5G |
| UWB | None | **Qorvo QM35825** (±5cm, 3D AoA, 4.08×3.38mm) | New; enables precise player tracking |
| Battery | 800mAh LiPo ($1.80) | **Enovix Silicon-Anode** (~1,100mAh equiv., ~$5.00) | +30–55% capacity; fast charge; same volume |
| PCB | 6-layer rigid | **8-layer LCP rigid-flex** | +20–30% PCB cost; enables antenna integration |
| Waterproofing | Parylene C | **ALD (10nm) + Parylene C (15µm)** | 100× better WVTR; IP68 rated |

### 7.2 Recommended v3 (2026–2027 Target)

| Function | v3 Recommendation | Rationale |
|----------|------------------|-----------|
| WiFi + BLE | **Infineon ACW741x** (WiFi 7, BLE 6.0, Thread) | Single chip; 70µW standby; MLO robustness for streaming |
| 5G | **Quectel RG255C successor / next-gen RedCap R18** | Further miniaturization expected |
| UWB | **Qorvo QM35825** (same) | Already best-in-class; stable platform |
| Battery | **NGK EnerCera tiled array** + Enovix primary cell | EnerCera enables ultra-thin backup layer; Enovix main cell |
| PCB | **MID housing + embedded 8-layer LCP PCB** | Max miniaturization; antennas in housing |

---

## 8. Form Factor Analysis — 70×45×4mm Patch

### 8.1 PCB Area Budget

Total internal area: **70 × 45 = 3,150 mm²**

| Component | Footprint (mm²) | % of Patch |
|-----------|----------------|-----------|
| RG255C-GL (5G RedCap) | 29×32 = 928 | 29.5% |
| Enovix battery (ref. 17.3×28.9mm) | 499 | 15.8% |
| CYW55913 (WiFi/BLE SoC) | 3.57×5.32 = 19 | 0.6% |
| nRF54L15 (BLE 6.0, WLCSP) | 2.4×2.2 = 5.3 | 0.2% |
| QM35825 (UWB SoC) | 4.08×3.38 = 13.8 | 0.4% |
| Biometric sensors + IMU | ~200 | 6.3% |
| Power management ICs | ~100 | 3.2% |
| Antenna regions, keepouts | ~500 | 15.9% |
| **Total active area** | **~2,265** | **71.9%** |
| **Margin** | **~885** | **28.1%** |

The v2 stack is **marginally feasible** in 70×45mm at 4mm depth. The largest constraint is the RG255C-GL at 29×32mm. The battery at 17×29mm is the second constraint. 3D stacking (chip-on-chip, PCB-in-package) can reclaim vertical space within the 4mm depth.

**Critical:** A dedicated RF layout engineer must design antenna keep-outs for 5G sub-6 (600MHz–3.8GHz), WiFi 6E (2.4/5/6 GHz), BLE (2.4 GHz), and UWB (6.5 and 8 GHz) — these require careful spatial separation and the LCP substrate enables this.

---

## 9. Key Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| 5G RedCap active TX power drain (500–800mA peak) | High | Implement buffer-and-burst transmission; duty cycle 5G |
| WiFi 6E 20MHz cap limits 4K throughput in congested stadiums | Medium | Primary video via 5G RedCap; WiFi for supplementary/local |
| Patch temperature during charging near skin | Medium | Enovix fast charge with thermal cutback; skin side thermal pad |
| 5G RedCap network availability (SA network required) | Medium | Fallback to LTE Cat-4 (RG255C supports this) |
| UWB regulatory (indoor +10dB allowance varies by region) | Low | QM35825 supports ETSI +10dB mode; FCC Part 15 compliant |
| EnerCera/Enovix supply chain (not commodity) | Medium | Dual-qualify Enovix + Sila Nano; LiPo fallback |
| CYW55913 BLE 5.4 vs 6.0 (no Channel Sounding) | Low | Add nRF54L15 if Channel Sounding is required |

---

## 10. Pricing Summary (Estimated @ 10K Units)

| Component | Current BOM | v2 BOM | Delta |
|-----------|------------|--------|-------|
| WiFi chip | $4.00 (RTL8852BE) | $4.50 (CYW55913) | +$0.50 |
| BLE chip | $4.00 (nRF5340) | $3.50 (nRF54L15) | -$0.50 |
| 5G module | — (vest, not patch cost) | $45–55 (RG255C-GL) | +$50 |
| UWB chip | — | $8–15 (QM35825 est.) | +$12 |
| Battery | $1.80 (LiPo) | $5.00 (Enovix) | +$3.20 |
| PCB (LCP RF) | Baseline | +30–40% | +$3–5 |
| Coating (ALD+Parylene) | Baseline | +20–30% | +$1–2 |
| **Estimated Total Delta** | | | **+~$70–80/unit** |

Note: 5G RedCap module dominates the cost increase. At scale (100K+ units), RG255C-GL pricing approaches $30–35/unit based on Qualcomm X35 chipset volume economics.

---

## 11. 2025–2026 Timeline & Availability

| Component | Status | Availability |
|-----------|--------|-------------|
| Infineon CYW55913 | Production | **Now** |
| Nordic nRF54L15 | Production (WLCSP) | **Now** |
| Nordic nRF54H20 | Sampling → Production | **2025** |
| Quectel RG255C-GL | Production | **Now** |
| Fibocom FG132 LGA | Production | **Now** |
| Qorvo QM35825 | Production (announced March 2025) | **2025** |
| NXP Trimension SR150 | Production | **Now** |
| Enovix Silicon-Anode (wearable) | Production | **Now (wearable format)** |
| Enovix AI-1 (wearable) | Production (scaling 2025) | **2025–2026** |
| Sila Nano Moses Lake supply | First commercial shipments | **Q3 2025** |
| NGK EnerCera (evaluation kits) | Sampling | **2025** |
| Infineon ACW741x (WiFi 7) | Sampling | **2026** |

---

## 12. Sources & References

1. [Infineon CYW55913 Product Page](https://www.infineon.com/part/CYW55913) — CYW55913 specs, 3.57×5.32mm size, WiFi 6E tri-band
2. [Infineon ACW741x WiFi 7 Launch](https://www.infineon.com/market-news/2026/infcss202601-039) — 70µW standby, 20MHz WiFi 7 IoT
3. [CNX Software ACW741x Deep Dive](https://www.cnx-software.com/2026/01/26/infineon-airoc-acw741x-wi-fi-7-ultra-low-power-tri-radio-iot-soc-family-support-mlo-wi-fi-sensing-ble-6-0-and-thread/) — Full ACW741x specs
4. [CYW55913 Mouser Datasheet](https://www.mouser.com/datasheet/2/196/Infineon_AIROC_TM_CYW55913_2_1_Connected_MCU_with_-3512217.pdf) — Full spec sheet
5. [Nordic nRF54L15 Product Page](https://www.nordicsemi.com/Products/nRF54L15) — BLE 6.0, Channel Sounding, 0.8µA sleep
6. [Nordic nRF54H20 Product Page](https://www.nordicsemi.com/Products/nRF54H20) — 1.7mA RX, 2MB NVM
7. [Silicon Labs EFR32BG27](https://www.silabs.com/wireless/bluetooth/efr32bg27-series-2-socs) — BLE 5.4 specs
8. [TI CC2340 Launch](https://www.allaboutcircuits.com/news/ti-rolls-out-bluetooth-le-mcu-with-8-dbm-rf-power-for-0.79/) — $0.79 BLE SoC
9. [Quectel RG255C Product](https://www.quectel.com/product/5g-redcap-rg255c-series/) — RedCap module page
10. [Quectel RG255C LGA Datasheet (DigiKey)](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/8893/Quectel_RG255C.pdf) — 29×32×2.4mm, power specs
11. [Fibocom FG132 Datasheet](https://www.m2mgermany.de/shop/media/webshop_dl/Fibocom/8071_Fibocom_FG132_Datasheet_V1.3.pdf) — FG132 LGA 29×32×2.4mm
12. [5G RedCap Explained 2025](https://spenza.com/telecom/what-is-5g-redcap-iot-iiot-guide-2025/) — 150Mbps DL, 50% power reduction
13. [Qorvo DW3220 Product](https://www.qorvo.com/products/p/DW3220) — <10cm accuracy, PDoA
14. [Qorvo QM35825 Product](https://www.qorvo.com/products/p/QM35825) — ±5cm, ±2° AoA, 4.08×3.38mm
15. [Qorvo QM35825 Press Release 2025](https://www.qorvo.com/newsroom/news/2025/qorvo-expands-ultra-wideband-portfolio-with-first-fully-integrated-low-power-soc) — First integrated UWB SoC
16. [NXP Trimension SR150](https://www.nxp.com/products/SR150) — FiRa certified, $3.96/1K units
17. [FiRa Consortium — UWB in Sports](https://www.firaconsortium.org/resource-hub/blog/how-ultrawideband-is-tackling-sports) — NFL/NBA UWB deployment
18. [UWB Sports Research 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11859737/) — Tennis UWB accuracy study
19. [Enovix AI-1 Launch](https://www.globenewswire.com/news-release/2025/07/07/3111025/0/en/Enovix-Launches-AI-1-A-Revolutionary-Silicon-Anode-Smartphone-Battery-Platform.html) — 935 Wh/L, 3C fast charge
20. [Enovix Wearable Cell Data Sheet](https://www.enovix.com/wp-content/uploads/2023/01/602d3e2d1b41897a1bb7c1c1_Enovix-Wearable-Cell-Data-Sheets.pdf) — 714 Wh/L, 340mAh cell
21. [Enovix Independent Testing](https://ir.enovix.com/news-releases/news-release-details/independent-testing-confirms-enovix-ai-1tm-achieves-935-whl/) — 935 Wh/L confirmed
22. [NGK EnerCera Wearables 2025](https://wearable-technologies.com/news/august-2025-ultra-thin-battery-revolution-in-wearables) — 0.45mm, non-swelling
23. [NGK EnerCera Evaluation Board](https://ipxchange.tech/evaluation-boards/ngk-enercera-pouch-bendable-li-ion-rechargeable-battery-evaluation-board/) — Capacity/specs table
24. [Sila Nano Moses Lake Plant](https://discoveryalert.com.au/silas-moses-lake-battery-innovation-2025/) — Q3 2025 wearable supply
25. [ProLogium Gen 4 LCB](https://prologium.com/prologium-shines-bright-at-ces-2025-with-fully-inorganic-electrolyte-battery-breakthroughs/) — 860–900 Wh/L solid-state
26. [ALD-Parylene IMAPS Study 2024](https://imapsource.org/article/129018-atomic-layer-deposition-parylene-conformal-nanocoatings-for-robust-corrosion-protection-of-electronics.pdf) — 100× WVTR improvement
27. [Forge Nano ALD for RF](https://www.forgenano.com/archivesite/atomic-layer-deposition-for-rf-devices/) — ALD hermetic sealing for PCBs
28. [P2i Nano-Coating](https://www.p2i.com/2016/10/13/maximising-water-proof-electronics-with-advanced-conformal-coatings/) — IPX8 conformal coating
29. [LCP Film for Wearables](https://www.samaterials.com/content/lcp-film-enabling-5g-wearables-and-aerospace-advances.html) — DC to 110GHz, <0.04% moisture
30. [Microwave Journal — LCP](https://www.microwavejournal.com/articles/6219-liquid-crystal-polymer-enabling-next-generation-conformal-and-multilayer-electronics) — LCP substrate RF properties
31. [MID Market 2026](https://www.businesswebwire.com/molded-interconnect-device-market/) — 3D antenna integration
32. [Nextwaves UWB Module Comparison](https://nextwaves.com/blog/the-ultimate-uwb-module-comparison-prices-specs-and-use-cases) — Pricing and specs survey

---

*Document generated June 2025 | AthleteView SmartPatch Hardware Research*  
*All prices are estimated and subject to volume negotiations. Specifications from manufacturer datasheets and verified secondary sources.*
