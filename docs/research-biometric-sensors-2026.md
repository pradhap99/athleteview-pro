# AthleteView SmartPatch — Biometric Sensor Research Report
**Project:** AthleteView — Body-Worn Sports Analytics Wearable Patch  
**Research Date:** 2025/2026  
**Purpose:** Identify best-in-class sensors to beat current specs across all modalities

---

## Executive Summary

The current AthleteView sensor stack is solid for 2022-era design, but five specific upgrades offer meaningful performance improvements. The single highest-impact change is replacing the PPG/SpO2 sensor with either the **MAX86178** (adds ECG + BioZ, same footprint) or the **ams AS7058** (8-LED/8-PD, higher SNR). For the IMU, the **ICM-45686** with BalancedGyro technology offers supreme vibration rejection and ±32g range — critical for cricket/football impacts. Temperature can be meaningfully upgraded to **ams AS6221** (±0.09°C best-in-class, 1.5×1.0mm). Environmental sensing has a compelling upgrade in **BMP585** (waterproof barometer) paired with **SHT45** (best-in-class humidity). For MEMS mic, **Infineon IM73A135V01** leads on SNR (73 dB) with IP57 waterproofing.

---

## 1. PPG / SpO2 Sensors

### 1.1 Current Baseline: MAX86141

| Parameter | MAX86141 |
|---|---|
| Architecture | Dual-channel optical PPG |
| LED channels | 2 drivers |
| PD channels | 2 |
| SNR | ~107 dB |
| Package | WLP 2.048×1.848mm |
| Est. price @10K | ~$4.50/unit |
| ECG/BioZ | No |
| Wavelengths | Green, Red, IR (LED selection by user) |

---

### 1.2 Candidate: MAX86178 (Analog Devices / Maxim)

**Best-in-class combo chip — strong upgrade path**

| Parameter | MAX86178 |
|---|---|
| Architecture | PPG + ECG + BioZ triple-modal AFE |
| LED channels | 6 LEDs (two 8-bit high-current drivers) |
| PD channels | 4 photodiode inputs, 2 optical readout channels |
| PPG SNR | **115 dB** (SpO2 system) / 112 dB @ 16µA |
| ECG ENOB | 15.3 ENOB, 0.72µV_RMS noise (0.05–40Hz) |
| BioZ | 17 ENOB, 0.16µV_RMS; 16Hz–500kHz BIA/BIS |
| ECG CMRR | >110 dB @ 50/60Hz |
| Active current | 16µA (PPG mode) |
| Shutdown current | 0.5µA |
| Package | WLP 2.77×2.57mm, 49-bump |
| Temp range | -40°C to +85°C |
| ADC resolution | 20-bit |
| FIFO | 256-word (synchronized ECG, PPG, BioZ) |
| Ambient rejection | >90 dB @ 120Hz with averaging |
| Est. price @1K | ~$5.45 (budgetary) |
| Interface | I2C, SPI |

**Key advantages over MAX86141:**
- Adds clinical-grade ECG and body impedance (respiration, hydration) in the same ~2.7mm footprint
- 115 dB SNR vs ~107 dB baseline — ~8 dB improvement in motion-artifact-prone environments
- Supports up to 6 LEDs: enables Green + Red + IR + additional wavelength (e.g., amber/blue for deeper tissue)
- 256-word FIFO with synchronized timestamps across all three modalities
- Designed to IEC 60601-2-47 ambulatory ECG compliance
- BioZ at 16–500 kHz enables body composition (hydration, fat %) and respiration rate

**Limitations:**
- Package is slightly larger than MAX86141 (2.77×2.57 vs 2.048×1.848mm)
- Does not integrate accelerometer (requires external IMU for motion compensation)
- No native multi-wavelength spectroscopy beyond 6-LED configuration

**Sports analytics unlocked:** ECG-gated PPG for blood pressure estimation via PTT/PAT; respiration rate via BioZ; body hydration via impedance spectroscopy

**Sources:** [Analog Devices MAX86178 Product Page](https://www.analog.com/en/products/max86178.html) | [MAX86178 Datasheet PDF](https://www.analog.com/media/en/technical-documentation/data-sheets/max86178.pdf) | [Mouser MAX86178](https://www.mouser.com/new/analog-devices/maxim-max86178/)

---

### 1.3 Candidate: ams OSRAM AS7058

**Best for maximum LED/PD flexibility and GSR sensing**

| Parameter | AS7058 |
|---|---|
| Architecture | PPG + ECG + BioZ + EDA (GSR) AFE |
| LED channels | 8 output pins, 2 drivers up to 300mA, 25/150/225/300mA ranges |
| PD channels | **8 photodiode input pins** |
| PPG SNR | **120 dB** FS (white card loopback test) |
| ECG noise | 0.68µV_RMS (lowest on market per ams) |
| ECG CMRR | ~118 dB |
| Active current | **<20µA @ 25 SPS** |
| Package | WLCSP 2.82×2.55×0.4mm, 42-pin |
| BioZ | 1kHz–1MHz, 200nA–100µA injection current |
| EDA/GSR | Yes — galvanic skin response for stress detection |
| ADC | Two 20-bit ADCs (PPG) + one 20-bit ADC (ECG/BioZ) |
| Interface | I²C (slave), SPI (16MHz) |
| Supply voltage | max 1.98V |

**Key advantages:**
- Highest PPG SNR in class at 120 dB — critical for motion artifact rejection
- 8 LEDs + 8 PDs allows narrow-band, optimized configurations across body locations
- GSR/EDA channel enables psychological stress monitoring (unique for sports)
- BioZ frequency up to 1 MHz for multi-frequency BIA (more precise body composition)
- Sub-20µA active current at 25 SPS — lowest power in class

**Limitations:**
- Requires external LED selection; fewer standalone reference designs than MAX86178
- 1.98V max supply constrains some system architectures
- Less ecosystem/application-note support than ADI/TI parts

**Sources:** [ams OSRAM AS7058 Product Page](https://ams-osram.com/products/sensor-solutions/analog-frontend/ams-as7058-high-performance-vital-sign-analog-frontend) | [AS7058 Datasheet PDF](https://look.ams-osram.com/m/6b2e246fe55145c1/original/AS7058-IC-for-PPG-ECG-and-body-impedance-measurement.pdf)

---

### 1.4 Candidate: ams OSRAM AS7038RB

**Specialized disposable oximeter variant**

| Parameter | AS7038RB |
|---|---|
| Architecture | PPG + ECG (Red/IR dedicated filter) |
| LED driver | 4x, max 100mA, 10-bit adjustable |
| Spectral range | 590–710nm + NIR 800–1050nm (peak 650nm / 950nm) |
| PPG noise | 80 dB |
| ECG noise | 50µV_pp @ 1kHz |
| ECG freq range | 0.67–40 Hz |
| Primary use | Disposable / reusable oximeter |

**Assessment:** Designed for disposable oximetry patches. Lower SNR than AS7058. Best for cost-sensitive single-use implementations, not performance-optimized sports analytics.

**Sources:** [AS7038RB Product Document PDF](https://look.ams-osram.com/m/95c6568d42b6bef4/original/AS7038GB_AS7038RB_PD000546_1-00.pdf)

---

### 1.5 Candidate: TI AFE4420

**Compact 4-LED/4-PD PPG front-end**

| Parameter | AFE4420 |
|---|---|
| Architecture | PPG-only AFE |
| LED channels | 4 LEDs (common anode, 50–200mA, 8-bit control) — extendable to 8 via SPDT |
| PD channels | 4 time-multiplexed photodiode inputs |
| Dynamic range | Up to 100 dB |
| Active current | 15µA LED + 20µA receiver (typical HRM) |
| Package | DSBGA 2.6×2.1mm, 0.4mm pitch (30-pin) |
| FIFO | 128 samples |
| Phases | Up to 16 signal phases |
| Interface | I2C / SPI |
| Temp range | -40°C to +85°C |
| Supply | Rx: 1.7–3.6V, Tx: 3–5.5V |

**Assessment:** Good compact option for PPG/SpO2-only designs. PPG-only (no ECG/BioZ). 100 dB dynamic range is lower than AS7058/MAX86178. Consider the newer **AFE4460** (16 phases, 32 LEDs, 4 PDs, 115 dB peak SNR, 2.6×2.6mm DSBGA) as a better upgrade if staying in TI ecosystem.

**Sources:** [TI AFE4420 Part Details](https://www.ti.com/product/AFE4420/part-details/AFE4420YZT) | [TI AFE4420 Datasheet PDF](https://www.ti.com/lit/gpn/AFE4420) | [TI AFE4460 Product Page](https://www.ti.com/product/AFE4460)

---

### 1.6 Candidate: TI AFE4900

**ECG + PPG combo**

| Parameter | AFE4900 |
|---|---|
| Architecture | Synchronized PPG + ECG |
| LED channels | 4 (common anode, up to 200mA) |
| PD channels | 3 time-multiplexed |
| Dynamic range | 100 dB |
| ECG noise | 2.5µV_rms (1Hz–150Hz at 1kHz data rate) |
| Package | DSBGA 2.6×2.1mm |
| FIFO | 128 samples (ECG + PPG) |
| Interface | I2C / SPI |
| Op temp | -20°C to +70°C |

**Assessment:** Legacy part (2017 release). Lacks BioZ. Lower ECG performance than MAX86178 (2.5µV vs 0.72µV noise). The MAX86178 or AS7058 are strictly better for new designs. Not recommended for new development.

**Sources:** [TI AFE4900 Datasheet PDF](https://www.ti.com/lit/gpn/AFE4900) | [Mouser AFE4900 PDF](https://www.mouser.com/datasheet/2/405/afe4900-1144976.pdf)

---

### 1.7 PPG/SpO2 Comparison Table

| Sensor | SNR (dB) | LED/PD | ECG | BioZ | EDA/GSR | Package (mm) | Active I | Est. @10K |
|---|---|---|---|---|---|---|---|---|
| **MAX86141** *(current)* | ~107 | 2/2 | ✗ | ✗ | ✗ | 2.05×1.85 | N/A | ~$4.50 |
| **MAX86178** | **115** | 6/4 | ✓ Clinical | ✓ 16Hz–500kHz | ✗ | 2.77×2.57 | 16µA | ~$5.50 est. |
| **ams AS7058** | **120** | 8/8 | ✓ 118dB CMRR | ✓ 1kHz–1MHz | ✓ | 2.82×2.55 | <20µA @25SPS | ~$6–8 est. |
| **AS7038RB** | 80 | 4/2 | ✓ (limited) | ✗ | ✗ | N/A | N/A | Low (disposable) |
| **AFE4420** | 100 | 4/4 | ✗ | ✗ | ✗ | 2.6×2.1 | 15µA LED+20µA Rx | ~$3–4 est. |
| **AFE4460** | 115 | 32/4 | ✗ | ✗ | ✗ | 2.6×2.6 | 15µA LED+15µA Rx | ~$3.50 est. |
| **AFE4900** | 100 | 4/3 | ✓ (basic) | ✗ | ✗ | 2.6×2.1 | N/A | Legacy |

### 1.8 PPG Recommendation

**Primary upgrade: MAX86178** — adds clinical ECG + BioZ to the existing PPG in a nearly identical WLP footprint, at modest cost premium. Unlocks blood pressure estimation (PTT), respiration, and body composition in a single chip — dramatically increasing the analytics value of AthleteView without adding PCB area.

**Alternative: ams AS7058** — choose if 8-LED spectral flexibility and GSR monitoring are prioritized. Best raw SNR (120 dB) for most demanding motion-artifact rejection use cases. Requires more optical system design effort.

---

## 2. Temperature Sensors

### 2.1 Current Baseline: MAX30208

| Parameter | MAX30208 |
|---|---|
| Accuracy | ±0.1°C |
| Resolution | 0.005°C |
| Interface | I2C |
| Est. price @10K | ~$2.40/unit |
| Package | WLP (small) |
| Application | Clinical skin temperature |

---

### 2.2 Candidate: ams AS6221

**Best-in-class accuracy — beats MAX30208**

| Parameter | AS6221 |
|---|---|
| Accuracy | **±0.09°C** (20–42°C) — best on market |
| Range | -40°C to +125°C (full); specified over 20–42°C for body/skin |
| Resolution | Not specified (sub-0.01°C implied) |
| Supply voltage | 1.71–3.6V |
| Active current | **6µA @ 4 Hz** |
| Package | **WLCSP 1.5×1.0mm** — smallest available |
| No calibration | Required? No — factory calibrated |
| Conversion time | 35ms |
| Interface | I2C (standard) |
| Alert | Integrated threshold interrupt |
| Est. price @10K | ~$1.50–2.00 est. (volume pricing competitive with MAX30208) |

**Key advantages over MAX30208:**
- ±0.09°C accuracy — 10% better than ±0.1°C baseline
- 1.5×1.0mm package — smallest digital temp sensor on market (saves ~30% PCB area vs MAX30208)
- 6µA at 4 SPS — ultra-low power for always-on skin temperature monitoring
- Specified across full supply voltage range (not just single point)

**Sources:** [ams AS6221 Press Release](https://www.businesswire.com/news/home/20201202005402/en/ams-Innovation-Delivers-the-Worlds-Most-Accurate-Digital-Temperature-Sensor-for-Wearable-Devices-and-Data-Centers) | [AS6221 Factsheet PDF](https://my.avnet.com/wcm/connect/edf195e3-09dc-4b84-abc3-8d8394f1f8c3/AS6221_FS001000_1-00.pdf)

---

### 2.3 Candidate: TI TMP117

**NIST-traceable, clinically validated skin temperature**

| Parameter | TMP117 |
|---|---|
| Accuracy (skin range) | ±0.1°C max (-20°C to +50°C) / ±0.05°C typical |
| Resolution | 16-bit, **0.0078°C** |
| Supply voltage | 1.8–5.5V |
| Active current | **3.5µA @ 1 Hz** |
| Shutdown current | 150nA |
| Package | 1.5×1.0mm (SOT-23 and DRV packages available) |
| NIST traceable | Yes |
| Long-term drift | ±0.03°C over 1000h at 150°C |
| Interface | I2C / SMBus |
| Averaging | Programmable 1–64 samples |
| Standards | ASTM E1112, ISO 80601 |
| Est. price @10K | ~$1.80–2.20 est. |

**Key advantages:**
- TMP117M medical variant specifically validates to ±0.1°C across 25–50°C (full athletic skin temperature range)
- Best resolution at 0.0078°C — 12.5× higher resolution than most competitors
- NIST traceability provides regulatory pathway
- Programmable averaging reduces noise without firmware overhead
- Very low power: 3.5µA active, 150nA shutdown

**Sources:** [TI TMP117 Wearable Design Guide](https://e2e.ti.com/support/wireless-connectivity/bluetooth-group/bluetooth/f/bluetooth-forum/898250/faq-cc2640r2f-how-do-i-design-an-accurate-and-thermally-efficient-wearable-temperature-monitoring-system) | [TI TMP117 Whitepaper PDF](https://www.ti.com/lit/pdf/sszt286)

---

### 2.4 Candidate: Melexis MLX90632

**Non-contact infrared — different use case**

| Parameter | MLX90632 |
|---|---|
| Accuracy | ±0.2°C (medical grade, 35–42°C skin range) |
| Resolution | 0.02°C |
| Measurement | Non-contact IR (50° FoV) |
| Package | 3×3mm SMD (SFN) |
| Interface | I2C |
| Application | Ear/forehead thermometer, smart glasses |

**Assessment:** Non-contact measurement is useful for ambient/garment-based surface thermometry, but for skin-contact patches the AS6221 and TMP117 provide better accuracy and smaller packages. The MLX90632's 3×3mm package is larger than ideal for a patch. Best reserved for auxiliary non-contact temperature measurement or fever detection from a distance.

**Sources:** [Melexis MLX90632 Product Page](https://www.melexis.com/en/product/mlx90632/miniature-smd-infrared-thermometer-ic) | [Mouser MLX90632](https://www.mouser.com/new/melexis/melexis-mlx90632-temperature-sensor/)

---

### 2.5 Temperature Sensor Comparison Table

| Sensor | Accuracy | Resolution | Package (mm) | Active I | Supply | Key Differentiator |
|---|---|---|---|---|---|---|
| **MAX30208** *(current)* | ±0.1°C | 0.005°C | WLP (small) | N/A | N/A | Clinical grade baseline |
| **ams AS6221** ✓ | **±0.09°C** | Sub-0.01°C | **1.5×1.0** | **6µA @4Hz** | 1.71–3.6V | Smallest package, best accuracy |
| **TI TMP117** | ±0.1°C max / ±0.05°C typ | **0.0078°C** | 1.5×1.0 | 3.5µA @1Hz | 1.8–5.5V | Best resolution, NIST traceable |
| **Melexis MLX90632** | ±0.2°C (med.) | 0.02°C | 3×3 | Higher | 2.6–3.6V | Non-contact IR |

### 2.6 Temperature Recommendation

**Primary recommendation: ams AS6221** — surpasses MAX30208 on accuracy (±0.09 vs ±0.1°C), matches on package size (1.5×1.0mm), and costs comparably at volume. The 10% accuracy improvement matters for clinical-grade core temperature estimation from skin contact.

**Secondary recommendation: TI TMP117** — if 0.0078°C resolution is important for tracking rapid skin temperature changes during exercise, or if NIST traceability is required for regulatory purposes.

**Dual-sensor option:** Deploy both AS6221 (contact temp) + MLX90632 (non-contact ambient/air temp) to enable skin-to-ambient delta calculation — useful for heat stress assessment.

---

## 3. IMU Sensors

### 3.1 Current Baseline: ICM-42688-P

| Parameter | ICM-42688-P |
|---|---|
| Type | 6-axis (accel + gyro) |
| Accel range | ±16g |
| Gyro range | ±2000 dps |
| Gyro noise | 2.8 mdps/√Hz |
| Accel noise | 70 µg/√Hz |
| Active I (6-axis LN) | 0.88 mA |
| Package | LGA-14, 2.5×3.0mm |
| Est. price @10K | ~$3.00/unit |
| On-chip features | APEX (pedometer, tap, tilt, WoM) |
| Interface | I3C, I2C, SPI |

**Critical limitation for sports:** ±16g accel range. Cricket fast bowling deliveries generate 25–40g; American football tackles 30–80g impact. Max range will clip data during peak impacts.

---

### 3.2 Candidate: TDK ICM-45686 ★ RECOMMENDED

**World-first BalancedGyro — purpose-built for high-vibration sports**

| Parameter | ICM-45686 |
|---|---|
| Type | 6-axis (accel + gyro) |
| Accel range | **±2/4/8/16/32g** — 2× baseline |
| Gyro range | **±15.625–4000 dps** — 2× baseline |
| Gyro noise | 3.8 mdps/√Hz |
| Accel noise | 70 µg/√Hz |
| Active I (6-axis LN) | **420µA** — 52% lower than ICM-42688-P |
| Active I (6-axis LP) | **220µA** — 75% lower than ICM-42688-P |
| Sleep current | 2.2µA |
| Package | 2.5×3.0×0.81mm (identical footprint to ICM-42688-P) |
| FIFO | 8KB |
| Shock tolerance | **20,000g** |
| Temperature stability | Gyro ±0.005°/s/°C (best-in-class) |
| Interface | I3C, I2C, SPI |
| On-chip features | APEX: pedometer, tap, tilt, WoM, free-fall, High-G detection, Low-G detection |
| FIFO resolution | 18/19-bit high-resolution |
| Magnetometer | Not integrated (external AKM AK09940A available in module form) |

**BalancedGyro technology:**
- First-of-kind MEMS architecture with dual balanced structures
- Eliminates vibration-rectification error (VRE) — critical for high-impact sports where competing sensors produce false readings from vibration cross-coupling
- Best-in-class immunity to out-of-band vibration induced noise
- Reduced sensor-to-sensor coupling enables tighter array designs

**Key advantages over ICM-42688-P:**
- ±32g accel range covers all known sports impact scenarios (cricket 40g, American football 80g with margin)
- ±4000 dps gyro handles maximum human rotation rates (baseball swing ~700–2000 dps)
- 420µA active current vs 880µA = 52% power reduction — critical for patch battery life
- Drop-in replacement (identical 2.5×3.0mm LGA-14 footprint)
- BalancedGyro vibration rejection — will maintain signal quality during high-intensity sports better than any competing consumer IMU

**Limitations:**
- 6-axis only; separate magnetometer chip needed for 9-axis (AKM AK09940A works well in module)
- No native sensor fusion (ST LSM6DSV16X has edge here)

**Sources:** [TDK ICM-45686 Product Page](https://invensense.tdk.com/products/motion-tracking/6-axis/icm-45686/) | [Avnet ICM-45686 Overview](https://my.avnet.com/abacus/products/new-products/npi/tdk-icm-45686-series-sensor/) | [Mouser ICM-45686 Price](https://www.mouser.com/ProductDetail/TDK-InvenSense/ICM-45686) — ~$4.28/unit @100

---

### 3.3 Candidate: ST LSM6DSV16X

**AI on-chip + sensor fusion — best for gesture/activity analytics**

| Parameter | LSM6DSV16X |
|---|---|
| Type | 6-axis (accel + gyro) + Qvar channel |
| Accel range | ±2/4/8/16g |
| Gyro range | ±125/250/500/1000/2000/4000 dps |
| Accel noise | ~70 µg/√Hz (ultra-low noise) |
| Active I (combo HP) | 0.65 mA |
| Package | LGA-14L, 2.5×3.0×0.83mm |
| FIFO | 4.5 KB |
| On-chip ML | Machine Learning Core (MLC) — user-configurable decision trees |
| Sensor fusion | Embedded Sensor Fusion Low Power (SFLP) — quaternion output |
| FSM | 8 Finite State Machines for custom gesture recognition |
| Qvar | Electric charge variation sensing — touch/swipe/tap detection, proximity sensing |
| ASC | Adaptive Self-Configuration — auto-reconfigures based on motion context |
| Interface | I2C, SPI, MIPI I3C |
| Est. price @1K | ~$2.98 |
| OIS/EIS | Triple-core architecture (UI + OIS + EIS channels) |

**Key advantages:**
- Only IMU with **embedded AI/ML** for on-chip activity classification (running, walking, sprinting — user-customizable)
- **SFLP sensor fusion** outputs quaternion/Euler angles without host processor overhead — reduces MCU processing burden in patch
- **Qvar** electrodes enable non-contact biopotential sensing (heart rate detection through the PCB) and user touch gestures
- ±4000 dps gyro range (same as ICM-45686)
- Adaptive Self-Configuration for automatic power mode switching based on detected activity

**Limitations:**
- Accel max range only ±16g — may clip during 30–80g football impacts (major concern for cricket/gridiron)
- No BalancedGyro vibration rejection
- No integrated magnetometer

**Sources:** [ST LSM6DSV16X Product Page](https://www.st.com/en/mems-and-sensors/lsm6dsv16x.html) | [SparkFun Application Note PDF](https://cdn.sparkfun.com/assets/0/a/c/c/9/an5763-lsm6dsv16x-6axis-imu-with-embedded-sensor-fusion-ai-qvar-for-highend-applications-stmicroelectronics.pdf)

---

### 3.4 Candidate: Bosch BMI323

**Cost-effective, low-power, I3C capable**

| Parameter | BMI323 |
|---|---|
| Type | 6-axis (accel + gyro) |
| Accel range | ±2/4/8/16g |
| Gyro range | ±125/250/500/1000/2000 dps |
| Active I (6-axis HP) | 790µA |
| Active I (6-axis LP) | 390µA |
| Active I (6-axis NM) | 690µA |
| Suspend current | 15µA |
| Package | LGA-14, 2.5×3.0×0.83mm |
| FIFO | 2KB |
| Interface | I3C (first Bosch IMU), I2C, SPI (10MHz) |
| On-chip features | Step counter, gesture, tap, orientation, WoM |
| Startup time | 2.5ms (fast start mode) |
| Temperature sensor | 16-bit on-chip |
| Est. price @10K | ~$2.50–2.80 est. (cost-effective) |
| Gyro self-cal | Not available (BMI270 has CRT; BMI323 does not) |

**Assessment:** Lower cost alternative with decent power reduction vs BMI160 predecessor. However, ±16g accel limit is problematic for high-impact sports, and ±2000 dps gyro misses the ±4000 dps of ICM-45686 and LSM6DSV16X. Good choice for lower-cost sensor variants but not recommended for premium sports analytics.

**Sources:** [Bosch BMI323 Launch Article](https://www.bosch-presse.de/pressportal/de/en/many-applications-made-easy-bosch-launches-cost-effective-motion-sensor-bmi323-247748.html) | [BMI323 Datasheet PDF](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi323-ds000.pdf)

---

### 3.5 Candidate: Bosch BMI270

**Ultra-low-power wrist-optimized**

| Parameter | BMI270 |
|---|---|
| Type | 6-axis (accel + gyro) |
| Accel range | ±16g |
| Gyro range | ±2000 dps |
| Active I (6-axis) | 685µA typ |
| Active I (accel only) | 10µA |
| Package | 2.5×3.0×0.8mm |
| Calibration | CRT (Component Re-Trimming) — motionless gyro self-calibration |
| On-chip features | Context/activity recognition (Wear OS certified), gesture recognition |
| FIFO | 2KB |

**Assessment:** Best suited for wrist-worn fitness trackers. The CRT motionless self-calibration is valuable for manufacturing, but ±16g/±2000 dps limits severely restrict sports analytics applications. Not recommended as primary IMU upgrade.

**Sources:** [Bosch BMI270 Launch](https://www.bosch-sensortec.com/en/news/bosch-launches-smart-ultra-low-power-imu-bmi270.html) | [Mouser BMI270](https://www.mouser.com/new/bosch/bosch-sensortec-bmi270/)

---

### 3.6 IMU Comparison Table

| Sensor | Accel Max | Gyro Max | 6-axis I | Package (mm) | On-chip AI | g-rating | Key Feature |
|---|---|---|---|---|---|---|---|
| **ICM-42688-P** *(current)* | ±16g | ±2000 dps | 0.88mA | 2.5×3.0 | APEX basic | 20,000g shock | Baseline |
| **ICM-45686** ★ | **±32g** | **±4000 dps** | **420µA** | 2.5×3.0 | APEX + High-G | **20,000g** | BalancedGyro, drop-in |
| **LSM6DSV16X** | ±16g | ±4000 dps | 650µA | 2.5×3.0 | MLC + FSM | N/A | AI/ML, SFLP fusion, Qvar |
| **BMI323** | ±16g | ±2000 dps | 790µA | 2.5×3.0 | Basic WoM | N/A | I3C, cost-effective |
| **BMI270** | ±16g | ±2000 dps | 685µA | 2.5×3.0 | Context/gesture | N/A | CRT self-cal, Wear OS |

### 3.7 IMU Recommendation

**Primary: ICM-45686** — drop-in replacement for ICM-42688-P with 2× accel range (±32g covers all sports impacts), 2× gyro range (±4000 dps), 52% lower power, and BalancedGyro™ vibration rejection that directly addresses motion artifact in the PPG chain. Same footprint = zero PCB redesign.

**Hybrid option:** ICM-45686 (primary, high-g motion) + LSM6DSV16X (secondary, always-on activity classification at ultra-low power) — dual-IMU architecture for premium AthleteView tiers where the LSM6DSV16X MLC runs sport classification while ICM-45686 handles precision high-frequency kinematics.

**9-axis upgrade:** Pair ICM-45686 with AKM AK09940A magnetometer (±1200µT, 18-bit, I2C) for full 9-axis AHRS. Both chips are available in pre-assembled modules.

---

## 4. Humidity / Environmental Sensors

### 4.1 Current Baseline: BME280

| Parameter | BME280 |
|---|---|
| Measurements | Temperature + Humidity + Pressure |
| Humidity accuracy | ±3% RH |
| Temperature accuracy | ±0.5°C |
| Pressure accuracy | ±1 hPa |
| Package | LGA-8, 2.5×2.5×0.93mm |
| Est. price @10K | ~$2.50/unit |
| Gas sensor | No |
| Response time (RH) | 1 s (τ63%) |

---

### 4.2 Candidate: Sensirion SHT45

**Best-in-class humidity accuracy for sweat detection**

| Parameter | SHT45 |
|---|---|
| Humidity accuracy | **±1.0% RH** (typ, 25–75%) — 3× better than BME280 |
| Temperature accuracy | **±0.1°C** (typ, 0–75°C) |
| Response time (RH) | **4s (τ63%) / 2s heater cycle** |
| Supply voltage | 1.08–3.6V |
| Average current | **0.4µA** (1 Hz) |
| Idle current | 80 nA |
| Package | **DFN 1.5×1.5×0.5mm** — smallest humidity sensor available |
| Interface | I2C FM+ |
| Heater | Integrated high-power heater (anti-condensation) |
| Qualification | JEDEC JESD47, NIST traceable, ISO 17025 calibration |
| Est. price @1K | ~$3.00 (vs ~$2.50 for SHT40, ~$5.50 at retail) |
| Condensing environment | Fully functional |
| CRC | Yes |

**Key advantages:**
- ±1% RH accuracy vs ±3% baseline — critical for quantifying sweat rate from humidity change
- 1.5×1.5mm is smaller than BME280's 2.5×2.5mm
- Integrated heater prevents false readings from condensation (important during post-exercise cooling)
- 0.4µA average current — negligible power draw
- Temperature measurement redundancy (±0.1°C) at no cost increase

**Limitation:** No pressure measurement — must be paired with a dedicated barometer if altitude tracking is needed.

**Sources:** [Sensirion SHT45 Product Page](https://sensirion.com/products/catalog/SHT45) | [Sensirion SHT45 Press Release](https://sensirion.com/company/news/press-releases-and-news/article/ultra-high-accuracy-sht45-humidity-and-temperature-sensor-availab) | [Adafruit SHT45](https://www.adafruit.com/product/5665)

---

### 4.3 Candidate: Bosch BME688

**VOC gas sensing for sweat metabolite detection**

| Parameter | BME688 |
|---|---|
| Measurements | Temperature + Humidity + Pressure + VOC gas |
| Humidity accuracy | ±3% RH |
| Temperature accuracy | ±0.5°C (0–65°C) |
| Pressure accuracy | ±0.6 hPa |
| VOC sensing | MOX gas sensor — detects H₂S (F1 score 0.92), ethanol, carbon monoxide, VOCs |
| Gas response time | <1s (τ33–63%) |
| Package | LGA-8, **3.0×3.0×0.93mm** |
| Supply voltage | 1.2–3.6V |
| ULP current | 90µA (full env sensing) |
| Active gas scan | 3.9mA (gas scan mode) |
| H2O current @1Hz | 1µA |
| Interface | I2C / SPI |
| AI classification | BME AI Studio for on-device pattern recognition |
| Est. price @10K | ~$3.50–4.50 est. |

**Sports-specific application:** Sweat VOC fingerprinting — ammonia (muscle protein catabolism / fatigue indicator), acetone (fat burning / ketosis), isoprene (cardiovascular stress). H₂S scanning F1 score of 0.92 is commercially validated.

**Limitation:** ±3% RH (same as BME280 — no improvement on humidity accuracy). Package (3.0×3.0mm) larger than SHT45. Gas scan power draw (3.9mA) significant for a patch.

**Sources:** [Bosch BME688 on Mouser](https://www.mouser.com/new/bosch/bosch-bme688-ai-gas-sensor/) | [Adafruit BME688](https://www.adafruit.com/product/5046)

---

### 4.4 Candidate: Bosch BMP585

**Waterproof barometer — purpose-built for sports**

| Parameter | BMP585 |
|---|---|
| Pressure range | 30–125 kPa |
| Absolute accuracy | **±30 Pa (typ)** / ±50 Pa max |
| Relative accuracy | **±6 Pa / 10kPa** (sub-centimeter altitude change detection) |
| RMS noise | **<0.1 Pa** (without LPF) |
| TCO | ±0.5 Pa/K |
| Temperature range | -40°C to +85°C |
| Long-term drift | ±0.2 hPa / 12 months |
| Water resistance | **Gel-filled cavity — IP68 waterproof** |
| Package | LGA-9 with metal lid, **3.25×3.25×1.86mm** |
| Active current | **1.3µA @ 1Hz** (lowest power in class) |
| Interface | I2C (FM+, 1MHz), SPI (12MHz), I3C (5MHz) |
| ODR | Up to 622 Hz (forced mode) |
| FIFO | 32 pressure samples |
| Supply | VDD 1.71–3.6V, VDDIO 1.08–3.6V |

**Key advantages over BME280:**
- Gel-filled cavity provides water/sweat/chemical resistance — BME280 is NOT waterproof and can be damaged by sweat ingress in a patch application
- Sub-centimeter altitude resolution detects individual push-up/pull-up reps
- 1.3µA active current vs BME280's higher current modes
- ±30 Pa absolute accuracy vs ±100 Pa (BME280) — significant improvement

**Sources:** [Bosch BMP585 News](https://www.bosch-sensortec.com/en/news/brand-new-robust-barometric-pressure-sensor-bmp585.html) | [Mouser BMP585](https://www.mouser.com/new/bosch/bosch-bmp585-pressure-sensor/)

---

### 4.5 Environmental Sensor Comparison Table

| Sensor | Humidity Acc. | Temp Acc. | Pressure | Gas/VOC | Package (mm) | Active I | Waterproof |
|---|---|---|---|---|---|---|---|
| **BME280** *(current)* | ±3% RH | ±0.5°C | ±1 hPa | No | 2.5×2.5 | 3.6µA | No |
| **SHT45** ★ | **±1.0% RH** | **±0.1°C** | No | No | **1.5×1.5** | **0.4µA** | No |
| **BME688** | ±3% RH | ±0.5°C | ±0.6 hPa | **Yes (VOC)** | 3.0×3.0 | 90µA–3.9mA | No |
| **BMP585** ★ | No | ±0.5°C | **±0.03 hPa** | No | 3.25×3.25 | **1.3µA** | **Yes (gel)** |

### 4.6 Environmental Recommendation

**Replace BME280 with a two-sensor architecture:**

1. **SHT45** — humidity + temperature with 3× better accuracy and smaller package. Critical for sweat detection algorithms.
2. **BMP585** — replace the pressure function. Gel-filled waterproofing is essential for a patch worn during swimming or heavy sweating. Sub-centimeter altitude resolution adds training rep-counting capability.

**Optional addition: BME688** — if sweat VOC analytics (ammonia, acetone, isoprene) are a Phase 2 roadmap item. Power consumption during gas scanning (3.9mA) is a barrier for continuous use, but periodic sampling during rest intervals is feasible.

**Combined SHT45 + BMP585 cost:** ~$3.00 + ~$2.00 = ~$5.00 est. vs $2.50 for BME280 alone. The waterproofing value of BMP585 alone justifies the premium.

---

## 5. MEMS Microphones

### 5.1 Current Baseline: SPH0645LM4H (Knowles)

| Parameter | SPH0645LM4H |
|---|---|
| SNR | ~65 dBA |
| AOP | 120 dB SPL |
| Interface | I2S PDM |
| Package | 3.5×2.65×0.98mm |
| Est. price @10K | ~$1.50/unit |
| Water resistance | Not rated |

---

### 5.2 Candidate: Infineon IM73A135V01 ★ RECOMMENDED

**Best SNR + IP57 waterproofing — ideal for sports patch**

| Parameter | IM73A135V01 |
|---|---|
| SNR (normal mode) | **73 dB(A) @ 2.75V** — best available |
| SNR (low power mode) | 71 dB(A) @ 1.6V |
| AOP (normal) | **135 dB SPL** (10% THD) |
| AOP (low power) | 130 dB SPL |
| Dynamic range | ~135 – (noise floor) = **246 dB range** |
| Current (normal) | 170µA @ 2.75V |
| Current (low power) | **70µA @ 1.6V** |
| Supply voltage | 1.52–3.0V |
| Interface | **Analog differential** |
| LFRO | **20 Hz** (flat response) |
| Group delay @ 1kHz | **2µs** |
| Phase matching | ±1 dB (excellent for beamforming) |
| Package | **4.0×3.0×1.2mm** |
| Water protection | **IP57 at component level** (Sealed Dual Membrane) |
| THD @ 94 dB SPL | 0.5% |

**IP57 is a game-changer for sports patches:** Microphone can be directly exposed to sweat, light rain, or submersion to 1m. No mesh or protective cover required, saving assembly cost and preserving acoustic performance.

**73 dB SNR vs 65 dB baseline = 8 dB improvement** — significant for acoustic analytics (impact detection, breathing rate, heartbeat auscultation).

**Differential analog output** requires a differential amplifier on the MCU/codec side — slightly more complex than digital PDM, but eliminates quantization noise at the mic level.

**Sources:** [Infineon IM73A135 Product Page](https://www.infineon.com/part/IM73A135) | [IM73A135V01 Datasheet PDF](https://www.infineon.com/dgdl/Infineon-MEMS_IM73A135V01-ProductBrief-v02_00-EN.pdf) | [Full Datasheet](https://www.infineon.com/dgdl/Infineon-IM73A135-DataSheet-v01_00-EN.pdf)

---

### 5.3 Candidate: TDK InvenSense T5838

**Best digital PDM option with always-on acoustic detection**

| Parameter | T5838 |
|---|---|
| SNR (HQ mode) | 68 dBA |
| SNR (LP mode) | 65 dBA |
| AOP (HQ mode) | 133 dB SPL |
| AOP (LP mode) | 119 dB SPL |
| Current (HQ) | 310–330µA |
| Current (LP/always-on) | **120–130µA** |
| Current (sleep) | 9µA |
| Current (AAD mode) | **20µA** |
| Interface | **PDM (digital)** |
| Package | 3.5×2.65×0.98mm |
| LFRO | 28 Hz |
| Modes | HQ / LP / Ultrasonic / Sleep + Acoustic Activity Detect |
| Water resistance | Not rated |
| AAD feature | Yes — hardware keyword/activity wake-on-sound |

**Acoustic Activity Detect (AAD):** Monitors acoustic environment at 20µA and wakes the host processor only when relevant sound is detected. Ideal for always-on breathing/heart rate acoustic monitoring on a patch that must extend battery life.

**Limitation:** 68 dBA SNR (5 dB below IM73A135). No IP rating — vulnerable in sweaty environments.

**Sources:** [TDK T5838 Mouser PDF](https://www.mouser.com/pdfDocs/TDK052_SmartSound.pdf) | [Syntiant/T5838 Analysis](https://www.syntiant.com/news/blog-post-title-three-mmhbm) | [EDOM Tech T5838](https://www.edomtech.com/en/product-detail/t5838-multi-mode-digital-microphone/)

---

### 5.4 MEMS Microphone Comparison Table

| Sensor | SNR | AOP | Active I | Package (mm) | Interface | IP | Key Feature |
|---|---|---|---|---|---|---|---|
| **SPH0645LM4H** *(current)* | 65 dBA | 120 dB | N/A | 3.5×2.65 | I2S PDM | None | Baseline |
| **IM73A135V01** ★ | **73 dBA** | **135 dB** | 170µA (70µA LP) | 4.0×3.0 | Analog diff. | **IP57** | Best SNR + waterproof |
| **T5838** | 68 dBA | 133 dB | 130µA LP / 20µA AAD | 3.5×2.65 | PDM | None | AAD always-on detect |
| **ICS-43434** | 65 dBA | 131 dB | 275µA | 3.35×2.50 | I2S | None | Smaller package |

### 5.5 Microphone Recommendation

**Primary: Infineon IM73A135V01** — 8 dB SNR improvement over baseline, highest AOP (135 dB SPL handles proximity to high-intensity impacts), and **IP57 waterproofing is mandatory** for a sports patch that must survive sweat, rain, and contact with wet surfaces. The analog differential interface is standard in any codec/MCU with differential ADC.

**Consideration:** If always-on voice/acoustic detection is needed at ultra-low power (e.g., breathing pattern analysis between plays), consider running both IM73A135 (acoustic capture) + T5838 in AAD mode (activity detector) in parallel. Combined quiescent draw remains manageable.

---

## 6. Bonus Sensors — Emerging Modalities

### 6.1 Bioimpedance / ECG Combo Chips

#### MAX30001 (Analog Devices)

| Parameter | MAX30001 |
|---|---|
| Channels | 1× ECG/biopotential + 1× BioZ |
| ECG ENOB | 15.9 bits, 3.1µV_pp noise |
| BioZ ENOB | 17 bits, 1.1µV_pp noise |
| Power (ECG) | **85µW @ 1.1V** |
| Power (BioZ) | 158µW @ 1.1V |
| Shutdown | 0.6µA |
| Package | WLP 30-bump |
| AC Dynamic Range | ECG 65mV_pp / BioZ 90mV_pp |
| DC offset tolerance | ±650mV — handles wide variety of dry electrodes |
| R-R detection | Built-in HW algorithm — no MCU needed for HR |
| Standards | IEC 60601-2-47 compatible |
| Application | Dedicated ECG patch, chest band HR, respiration |

**Assessment vs MAX86178:** The MAX30001 is a dedicated ECG+BioZ-only chip (no PPG). It offers 85µW — lowest power ECG AFE on the market. Best for architectures where ECG is a primary sensor (chest-worn patch). For AthleteView, the MAX86178 already integrates ECG+BioZ+PPG — the MAX30001 would only be relevant if a separate discrete ECG electrode pair (chest location) is used alongside an optical PPG.

**Sources:** [Analog Devices MAX30001 Product Page](https://www.analog.com/en/products/max30001.html) | [Mouser MAX30001](https://www.mouser.com/new/analog-devices/maxim-max30001-afe/)

---

### 6.2 Sweat Electrolyte Sensors

No ASIC-level integrated sweat electrolyte chip exists in mass production (2025). Current state of technology:

**Commercial solution: Epicore Biosystems**
- Microfluidic sweat patch with screen-printed electrochemical electrodes
- Measures: Na⁺, K⁺, sweat rate, total sweat loss, skin temperature, motion
- Secured $26M Series B (Feb 2025), partnered with 3M/Innovize for manufacturing scale-up
- Gatorade Gx Sweat Patch: colorimetric Na⁺/Cl⁻ (no ASIC)
- Connected Hydration: real-time electrochemical measurement
- Technology requires microfluidic channel integration into the patch substrate — not a drop-in chip

**Research-grade (2025):**
- BMS3 (Science Advances, 2025): multi-day sweat sensor with Janus membrane, IP module for induced sweating, detects uric acid + xanthine + alcohol (gout management focus). Custom fabrication, not commercial.
- Typical measurable analytes: Na⁺ (20–100 mM), K⁺ (3–12 mM), lactate (0.5–20 mM), glucose (10µM–1mM), NH₄⁺, Cl⁻

**Integration recommendation for AthleteView:** Partner with Epicore Biosystems or license their microfluidic architecture. Screen-printed ISE (ion-selective electrode) for Na⁺/K⁺ + enzyme electrode for lactate can be co-fabricated on the patch flex substrate alongside the main PCB. Electrochemical readout ASIC options: Texas Instruments LMP91000 or Analog Devices AD5940 (configurable impedance/electrochemical measurement AFE).

**Sources:** [Epicore Biosystems $26M Series B](https://www.mobihealthnews.com/news/epicore-biosystems-scores-26m-expand-sweat-sensing-wearable-technology) | [BMS3 Science Advances 2025](https://www.science.org/doi/10.1126/sciadv.adw9024) | [Wearable Electrochemical Sensors Review (Nature)](https://www.nature.com/articles/s41378-022-00443-6)

---

### 6.3 Muscle Oxygen (SmO2) Sensors

**Technology:** Near-infrared spectroscopy (NIRS) at 760nm and 850nm wavelengths — differential absorption by oxygenated (HbO2) vs deoxygenated (Hb) hemoglobin.

**Commercial devices:**
- **Moxy Monitor** — matchbook-sized NIRS sensor, used by Olympic-level athletes including Kristian Blummenfelt (Olympic triathlon gold medalist). 63.5g, worn over target muscle
- **Train.Red FYER 2.0** — smaller factor SmO2 sensor
- No current single-chip NIRS AFE integrating driver, PD, and signal processing exists at consumer patch scale

**What's needed for patch integration:**
- Two NIR LEDs: 760nm + 850nm (or 730nm + 850nm)
- High-sensitivity photodiode with 2–4cm source-detector separation for muscle depth penetration
- Front-end: MAX86178 or AS7058 can drive the LEDs and read the PD signal — the AFE hardware is largely solved
- Algorithm: Requires modified Beer-Lambert law computation for tissue oxygenation — computationally feasible on patch MCU (e.g., Nordic nRF5340)
- Form factor challenge: SmO2 requires 3–5cm² sensing area for adequate source-detector geometry — feasible on a back/arm patch but challenging on a small wrist patch

**Chip-based NIRS (2025 research):** A PubMed-indexed study (May 2025) demonstrates chip-based NIRS sensor integration into a physical interface for SmO2 monitoring during static and dynamic exercise, with "preliminary results demonstrating sensor sensitivity to oxygenation changes." Commercial chip not yet available.

**Recommendation:** SmO2 can be prototyped with MAX86178 + external 760nm/850nm LEDs at 3–5cm separation on a larger patch format. Full integration as a dedicated chip is 2–3 years from commercialization.

**Sources:** [Outside Online Moxy/SmO2 Feature](https://www.outsideonline.com/health/training-performance/muscle-oxygen-moxy-sensor/) | [NIRS SmO2 Research Review (Spectroscopy Online)](https://www.spectroscopyonline.com/view/wearable-near-infrared-technology-tested-for-monitoring-athletic-performance) | [Chip-based NIRS Integration (PubMed 2025)](https://pubmed.ncbi.nlm.nih.gov/40644076/)

---

### 6.4 Strain Gauges / Force Measurement

**Current wearable options:**
- **Flexible piezoresistive strain gauges** — screen-printable on patch substrate, measures skin deformation/strain correlating to muscle activation. No ASIC needed — direct analog voltage output read by patch ADC.
- **MEMS piezoresistive pressure sensors** — Bosch BMP585 (covered above) provides barometric pressure but not contact force
- **Piezoelectric PVDF film** — generates voltage on deformation, passive sensing, no power required. Used in respiratory rate monitoring
- Research application: Flex/strain sensor over muscle belly or tendon to infer contraction force; over joint to infer angular position

**Relevance to AthleteView:** Strain sensing on the patch could detect impact events, respiratory motion, and potentially muscle activity patterns. Integration is primarily a substrate/materials choice, not a chip selection. Recommend exploring Canatu CNB (carbon nanotube film) or Loctite/Henkel printed strain gauge inks for the patch substrate.

---

## 7. Comprehensive Recommendations Summary

### 7.1 Upgraded Sensor Stack — AthleteView v2.0

| Modality | Current | Recommended Upgrade | Delta Cost @10K | Key Gain |
|---|---|---|---|---|
| **PPG/SpO2/ECG** | MAX86141 (~$4.50) | **MAX86178** (~$5.50 est.) | +$1.00 | ECG + BioZ added; 115 dB SNR; 6 LEDs |
| **Temperature** | MAX30208 (~$2.40) | **ams AS6221** (~$1.80 est.) | -$0.60 | ±0.09°C vs ±0.1°C; 1.5×1.0mm |
| **Humidity** | BME280 (~$2.50) | **SHT45** (~$3.00) | +$0.50 | ±1% RH vs ±3%; 1.5×1.5mm |
| **Barometer** | BME280 (included above) | **BMP585** (~$2.00 est.) | See note | Waterproof gel; sub-cm altitude |
| **IMU** | ICM-42688-P (~$3.00) | **ICM-45686** (~$3.50 est.) | +$0.50 | ±32g; ±4000dps; BalancedGyro; 52% less power |
| **MEMS Mic** | SPH0645LM4H (~$1.50) | **IM73A135V01** (~$2.20 est.) | +$0.70 | 73 dB SNR +8dB; IP57 waterproof |

**Note on BME280 replacement:** The BME280 covered humidity + pressure in one chip at $2.50. Replacing with SHT45 ($3.00) + BMP585 ($2.00) = $5.00 total, or +$2.50 vs current. The waterproofing of BMP585 is operationally necessary for a patch — the BME280's non-hermetic pressure port is vulnerable to sweat ingress and will fail in field conditions.

**Total sensor BOM delta:** approximately +$4.10/unit @10K volume for the full v2.0 stack. For a professional sports analytics device, this is defensible.

---

### 7.2 Phased Roadmap

**Phase 1 (immediate, drop-in compatible):**
- IMU: ICM-42688-P → **ICM-45686** (same LGA-14 footprint, no PCB change)
- Temperature: MAX30208 → **ams AS6221** (same WLP footprint, I2C compatible)
- MEMS Mic: SPH0645 → **IM73A135V01** (similar footprint, PDM→analog differential change)

**Phase 2 (next PCB spin):**
- PPG/SpO2: MAX86141 → **MAX86178** (WLP slightly larger; adds ECG electrode traces to layout)
- Environmental: BME280 → **SHT45 + BMP585** (two smaller chips replace one)

**Phase 3 (new modalities):**
- Add **BME688** for sweat VOC analytics (ammonia/acetone/isoprene) — enable fatigue and metabolic state detection
- Integrate **sweat electrolyte electrodes** (Na⁺/K⁺/lactate) via microfluidic channel using AD5940 or LMP91000 as readout AFE
- Evaluate **SmO2 muscle oxygen** via dual-wavelength NIR approach using MAX86178 with 760nm + 850nm LEDs

---

### 7.3 Power Budget Comparison

| Sensor | Current Power | Upgraded Power | Saving |
|---|---|---|---|
| PPG AFE | ~2–5mA active | ~2–3mA (MAX86178 @ 16µA quiescent) | Marginal |
| Temperature | ~50µA | **6µA (AS6221)** | ~87% |
| Humidity | ~750µA | **0.4µA (SHT45)** | ~99.9% |
| Barometer | ~714µA | **1.3µA (BMP585)** | ~99.8% |
| IMU | 880µA | **420µA (ICM-45686)** | **52%** |
| Microphone | N/A | 70µA LP (IM73A135) | — |

The largest cumulative power saving is from the environmental sensors (SHT45 + BMP585 replace BME280's multi-hundred µA modes) and IMU. These directly extend patch operational time between charges.

---

## 8. Technical Notes

### Motion Artifact Rejection Architecture

For sports use, the critical motion artifact rejection chain is:
1. **Mechanical:** Firm patch adhesion with flexible PCB substrate to minimize relative motion between optics and skin
2. **Hardware:** High ambient light rejection (MAX86178: >90 dB @ 120Hz; AS7058: Advanced Ambient Offset Control)
3. **Temporal:** Synchronized IMU data timestamps with PPG samples — both MAX86178 (256-word FIFO with timing data) and ICM-45686 (8KB FIFO with 18-bit timestamps) support microsecond-level synchronization
4. **Algorithmic:** Accelerometer reference subtraction (NLMS, LMS, or deep learning-based) using ICM-45686 accel data to remove motion baseline from PPG signal

### ECG in a Patch Context

Adding ECG via MAX86178 requires two skin electrodes plus ground. For a sports patch, options include:
- Flex PCB exposed electrode pads with conductive hydrogel interface (highest quality)
- Conductive ink printed electrodes on patch edges (lower cost, suitable for single-use)
- Textile electrode integration for multi-wear patches

ECG IEC 60601-2-47 compliance (supported by MAX86178) will be needed for any regulatory submission in EU/US clinical markets.

### Sweat-Proofing Priority

A body-worn sports patch during competition will be exposed to sustained heavy sweating. Sensor selection must account for ingress protection:
- **BMP585** — gel-filled cavity, IP68 rated — mandatory upgrade for pressure sensing
- **IM73A135** — IP57 at component level — eliminates need for acoustic membrane
- **SHT45** — condensing-environment rated — validated in high-humidity
- Other sensors (PPG AFE, IMU, temp) are die-level sealed; patch conformal coating or encapsulation handles remaining protection

---

## Sources

| Source | URL |
|---|---|
| Analog Devices MAX86178 Product Page | https://www.analog.com/en/products/max86178.html |
| MAX86178 Datasheet PDF | https://www.analog.com/media/en/technical-documentation/data-sheets/max86178.pdf |
| ams OSRAM AS7058 Product Page | https://ams-osram.com/products/sensor-solutions/analog-frontend/ams-as7058-high-performance-vital-sign-analog-frontend |
| AS7058 Datasheet PDF | https://look.ams-osram.com/m/6b2e246fe55145c1/original/AS7058-IC-for-PPG-ECG-and-body-impedance-measurement.pdf |
| AS7038RB Product Document | https://look.ams-osram.com/m/95c6568d42b6bef4/original/AS7038GB_AS7038RB_PD000546_1-00.pdf |
| TI AFE4420 Part Details | https://www.ti.com/product/AFE4420/part-details/AFE4420YZT |
| TI AFE4460 Product Page | https://www.ti.com/product/AFE4460 |
| TI AFE4900 Datasheet | https://www.ti.com/lit/gpn/AFE4900 |
| ams AS6221 Announcement (BusinessWire) | https://www.businesswire.com/news/home/20201202005402/en/ams-Innovation-Delivers-the-Worlds-Most-Accurate-Digital-Temperature-Sensor-for-Wearable-Devices-and-Data-Centers |
| AS6221 Factsheet PDF | https://my.avnet.com/wcm/connect/edf195e3-09dc-4b84-abc3-8d8394f1f8c3/AS6221_FS001000_1-00.pdf |
| TI TMP117 Wearable Design Guide | https://e2e.ti.com/support/wireless-connectivity/bluetooth-group/bluetooth/f/bluetooth-forum/898250/faq-cc2640r2f-how-do-i-design-an-accurate-and-thermally-efficient-wearable-temperature-monitoring-system |
| TI TMP117 Whitepaper PDF | https://www.ti.com/lit/pdf/sszt286 |
| Melexis MLX90632 Product Page | https://www.melexis.com/en/product/mlx90632/miniature-smd-infrared-thermometer-ic |
| TDK ICM-45686 Product Page | https://invensense.tdk.com/products/motion-tracking/6-axis/icm-45686/ |
| Avnet ICM-45686 Overview | https://my.avnet.com/abacus/products/new-products/npi/tdk-icm-45686-series-sensor/ |
| Mouser ICM-45686 Pricing | https://www.mouser.com/ProductDetail/TDK-InvenSense/ICM-45686 |
| ICM-45686 BalancedGyro Analysis | https://www.silintech.com/index.php/en/news/112-balancedgyro-tdk-icm-45686-mems |
| ST LSM6DSV16X Product Page | https://www.st.com/en/mems-and-sensors/lsm6dsv16x.html |
| LSM6DSV16X SparkFun App Note | https://cdn.sparkfun.com/assets/0/a/c/c/9/an5763-lsm6dsv16x-6axis-imu-with-embedded-sensor-fusion-ai-qvar-for-highend-applications-stmicroelectronics.pdf |
| Bosch BMI323 Launch | https://www.bosch-presse.de/pressportal/de/en/many-applications-made-easy-bosch-launches-cost-effective-motion-sensor-bmi323-247748.html |
| BMI323 Datasheet PDF | https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi323-ds000.pdf |
| Bosch BMI270 Launch | https://www.bosch-sensortec.com/en/news/bosch-launches-smart-ultra-low-power-imu-bmi270.html |
| Sensirion SHT45 Product Page | https://sensirion.com/products/catalog/SHT45 |
| Sensirion SHT45 Press Release | https://sensirion.com/company/news/press-releases-and-news/article/ultra-high-accuracy-sht45-humidity-and-temperature-sensor-availab |
| Bosch BME688 on Mouser | https://www.mouser.com/new/bosch/bosch-bme688-ai-gas-sensor/ |
| Bosch BMP585 News | https://www.bosch-sensortec.com/en/news/brand-new-robust-barometric-pressure-sensor-bmp585.html |
| Mouser BMP585 | https://www.mouser.com/new/bosch/bosch-bmp585-pressure-sensor/ |
| Infineon IM73A135 Product Page | https://www.infineon.com/part/IM73A135 |
| IM73A135V01 Product Brief PDF | https://www.infineon.com/dgdl/Infineon-MEMS_IM73A135V01-ProductBrief-v02_00-EN.pdf |
| IM73A135V01 Full Datasheet | https://www.infineon.com/dgdl/Infineon-IM73A135-DataSheet-v01_00-EN.pdf |
| TDK T5838 Mouser Press PDF | https://www.mouser.com/pdfDocs/TDK052_SmartSound.pdf |
| T5838 Syntiant Analysis | https://www.syntiant.com/news/blog-post-title-three-mmhbm |
| Analog Devices MAX30001 Product Page | https://www.analog.com/en/products/max30001.html |
| Epicore Biosystems $26M Series B | https://www.mobihealthnews.com/news/epicore-biosystems-scores-26m-expand-sweat-sensing-wearable-technology |
| BMS3 Sweat Sensor - Science Advances | https://www.science.org/doi/10.1126/sciadv.adw9024 |
| Wearable Electrochemical Sensors Review | https://www.nature.com/articles/s41378-022-00443-6 |
| Outside Online Moxy/SmO2 | https://www.outsideonline.com/health/training-performance/muscle-oxygen-moxy-sensor/ |
| NIRS SmO2 Sports Review | https://www.spectroscopyonline.com/view/wearable-near-infrared-technology-tested-for-monitoring-athletic-performance |
| Chip-based NIRS Integration PubMed 2025 | https://pubmed.ncbi.nlm.nih.gov/40644076/ |
| Wearable Smart Patches Dec 2024 | https://wearable-technologies.com/news/december-2024-remote-health-with-smart-patches |
