# AthleteView SmartPatch v3.0 — Hardware Upgrade Summary

## CURRENT BOM (v2.0) vs RECOMMENDED BOM (v3.0)

### 1. Camera Sensor
- CURRENT: Sony IMX577 (12MP, 1/2.3", 4K@30fps, $12/unit @10K)
- NEW: Sony IMX415 (8.46MP, 1/2.8", 4K@60fps, $4-6/unit @10K)
- GAIN: 38% smaller, 2x frame rate, 50-65% cheaper, 0.02 lux low-light
- FUTURE: Sony IMX678 (STARVIS 2, 0.13 lux, 2.0µm pixels) for Gen 2
- Sources: Sony, Leopard Imaging, e-consystems

### 2. SoC/NPU
- CURRENT: Rockchip RV1106G2 (Cortex-A7, 0.5 TOPS, $5.50/unit)
- NEW: Rockchip RV1106G3 (Cortex-A7, 1.0 TOPS, 256MB RAM, $5-7/unit)
- GAIN: 2x NPU, 2x RAM, pin-compatible drop-in upgrade, 8MP ISP
- ALT: Allwinner V853 (1.0 TOPS, $3.54-5.32 LCSC) — cheaper alternative
- ALT: Sophon SG2002 (1 TOPS, 10x10mm, RISC-V/ARM hybrid) — smallest

### 3. PPG/SpO2/ECG/BioZ Sensor
- CURRENT: MAX86141 (PPG only, 107dB SNR, 2.05x1.85mm, $4.50)
- NEW: MAX86178 (PPG+ECG+BioZ, 115dB SNR, 2.77x2.57mm, ~$5.50)
- GAIN: Adds ECG (clinical-grade, IEC 60601-2-47), BioZ (respiration, hydration), 6 LED/4 PD, +8dB SNR, synchronized timestamps
- ALT: ams AS7058 (120dB SNR, 8 LED/8 PD, GSR/EDA) — best raw SNR
- Datasheet: https://www.analog.com/en/products/max86178.html

### 4. IMU
- CURRENT: ICM-42688-P (±16g, ±2000dps, 880µA, LGA-14, $3.00)
- NEW: ICM-45686 (±32g, ±4000dps, 420µA, LGA-14 same footprint, ~$3.50)
- GAIN: 2x g-range (covers cricket/football impacts), 2x gyro range, 52% less power, BalancedGyro™ vibration rejection, drop-in replacement
- Source: https://invensense.tdk.com/products/motion-tracking/6-axis/icm-45686/

### 5. Temperature
- CURRENT: MAX30208 (±0.1°C, I2C, $2.40)
- NEW: ams AS6221 (±0.09°C, 1.5x1.0mm, 6µA @4Hz, ~$1.50-2.00)
- GAIN: Better accuracy, 40% smaller, lower power
- Source: https://www.businesswire.com/news/home/20201202005402/en/

### 6. Humidity
- CURRENT: BME280 (±3% RH, combo sensor, $2.50)
- NEW: Sensirion SHT45 (±1.0% RH, 1.5x1.5mm, 0.4µA) + Bosch BMP585 (gel-sealed waterproof baro)
- GAIN: 3x humidity accuracy, waterproof barometer (BME280 pressure port fails in sweat)
- SHT45 source: https://sensirion.com/products/catalog/SHT45
- BMP585 source: https://www.bosch-sensortec.com/en/news/brand-new-robust-barometric-pressure-sensor-bmp585.html

### 7. WiFi
- CURRENT: RTL8852BE (WiFi 6, 2x2, $4.00) + nRF5340 (BLE 5.3, $4.00) = 2 chips, $8
- NEW: Infineon CYW55913 (WiFi 6E + BLE 5.4, 3.57x5.32mm, ~$3.50-5.00)
- GAIN: Eliminates separate BLE chip, adds 6GHz band, 192MHz MCU onboard, Matter support
- FUTURE: Infineon ACW741x (WiFi 7 + BLE 6.0, 70µW standby) — sampling 2026

### 8. BLE (Dedicated)
- CURRENT: nRF5340 (BLE 5.3, 7x7mm, $4.00) — ELIMINATED if using CYW55913
- NEW: Nordic nRF54L15 (BLE 6.0, Channel Sounding, 2.4x2.2mm WLCSP, ~$3.50)
- GAIN: BLE 6.0, ±10cm ranging, 1/9th footprint, 50% lower RX power, RISC-V coprocessor
- ROLE: Dedicated BLE 6.0 + Channel Sounding for player ranging; CYW55913 handles WiFi
- Source: https://www.nordicsemi.com/Products/nRF54L15

### 9. 5G Cellular
- CURRENT: Quectel RM500Q (full 5G, 52x30mm, vest-only, 3-4W active)
- NEW: Quectel RG255C-GL (5G RedCap, 29x32x2.4mm LGA, 223Mbps DL, 2.5mA sleep)
- GAIN: Fits IN the patch (no separate vest for streaming), 50% less power, sufficient for 4K H.265 streaming
- Source: https://www.quectel.com/product/5g-redcap-rg255c-series/

### 10. UWB (NEW — Player Tracking)
- CURRENT: None
- NEW: Qorvo QM35825 (4.08x3.38mm BGA, ±5cm ranging, ±2° 3D AoA, FiRa 3.0, Cortex-M33)
- GAIN: Centimeter-precision player tracking in stadium, works with NXP SR150 anchors ($3.96/unit)
- Source: https://www.qorvo.com/products/p/QM35825

### 11. MEMS Microphone
- CURRENT: SPH0645LM4H (65dB SNR, $1.50)
- NEW: Infineon IM73A135V01 (73dB SNR, 135dB AOP, IP57 waterproof, ~$1.20-1.50)
- GAIN: +8dB SNR, component-level waterproofing (no mesh needed), higher AOP for stadium noise
- Source: https://www.infineon.com/part/IM73A135

### 12. Battery
- CURRENT: 800mAh LiPo pouch ($1.80)
- NEW: Enovix silicon-anode (935 Wh/L, ~1100-1240mAh same volume, 50% charge in 12min)
- GAIN: +30-55% capacity in same form factor, fast charging
- ALT: NGK EnerCera (0.45mm semi-solid-state) for ultra-thin designs
- Source: https://ir.enovix.com/news-releases/

### 13. PCB
- CURRENT: 6-layer rigid-flex, FR4+polyimide
- NEW: 8-layer LCP rigid-flex (LCP flex sections for RF, FR4 rigid for SoC)
- GAIN: LCP enables integrated antennas (WiFi 6E/UWB/5G), <0.04% moisture absorption

### 14. Waterproofing
- CURRENT: Parylene C only ($0.60 @10K)
- NEW: ALD Al₂O₃ (10nm) + Parylene C (15µm) dual-stack
- GAIN: 100x better WVTR, functional IP68 hermetic seal, eliminates pinholes
- ALT: P2i Barrier Max nano-coating for faster/cheaper processing

## BOM COST COMPARISON (estimated @10K units)

| # | Component | v2.0 Part | v2.0 Cost | v3.0 Part | v3.0 Cost |
|---|-----------|-----------|-----------|-----------|-----------|
| 1 | Camera | IMX577 | $12.00 | IMX415 | $5.00 |
| 2 | SoC | RV1106G2 | $4.50 | RV1106G3 | $5.50 |
| 3 | PPG/ECG/BioZ | MAX86141 | $4.50 | MAX86178 | $5.50 |
| 4 | IMU | ICM-42688-P | $3.00 | ICM-45686 | $3.50 |
| 5 | Temperature | MAX30208 | $2.40 | AS6221 | $1.80 |
| 6 | Humidity | BME280 | $2.50 | SHT45 | $1.50 |
| 7 | Barometer | (in BME280) | $0 | BMP585 | $1.80 |
| 8 | WiFi+BLE | RTL8852BE+nRF5340 | $8.00 | CYW55913 | $4.50 |
| 9 | BLE 6.0 | (in nRF5340) | $0 | nRF54L15 | $3.50 |
| 10 | 5G | RM500Q (vest) | $35.00 | RG255C-GL (patch) | $25.00 |
| 11 | UWB | None | $0 | QM35825 | $4.50 |
| 12 | MEMS Mic | SPH0645LM4H | $1.50 | IM73A135V01 | $1.30 |
| 13 | Battery | 800mAh LiPo | $1.80 | Enovix Si-anode | $3.50 |
| 14 | PCB | 6-layer rigid-flex | $4.50 | 8-layer LCP flex | $6.00 |
| 15 | Waterproofing | Parylene C | $0.60 | ALD+Parylene | $1.20 |
| 16 | PMIC+crystal | RK809-2 | $0.90 | RK809-2 | $0.90 |
| 17 | Passives | Various | $3.50 | Various | $3.50 |
| 18 | ESD/misc | Various | $1.10 | Various | $1.10 |
| 19 | Adhesive | 3M/Lohmann | $0.40 | 3M/Lohmann | $0.40 |
| 20 | Connector | Molex/Hirose | $0.75 | Molex/Hirose | $0.75 |
| 21 | Packaging | Custom | $1.00 | Custom | $1.00 |
| TOTAL | | | ~$87.95* | | ~$81.75* |

*Note: v2.0 total includes vest-unit 5G ($35); v3.0 integrates 5G into patch. Without 5G, patch-only v2.0 was ~$52.95; v3.0 patch-only with 5G+UWB = ~$81.75. The v3.0 eliminates the vest unit entirely.

## KEY ARCHITECTURAL CHANGES v2.0 → v3.0

1. **Vest eliminated** — 5G RedCap (RG255C-GL) moves INTO the patch
2. **Single patch does everything** — camera, AI, biometrics, 5G, WiFi, BLE, UWB
3. **3 new analytics modalities** — ECG, BioZ (hydration/respiration), UWB tracking
4. **WiFi+BLE consolidation** — CYW55913 replaces 2 chips; nRF54L15 adds BLE 6.0 ranging
5. **IP68 waterproofing** — ALD+Parylene dual-stack vs Parylene-only
6. **55% more battery** — Enovix silicon-anode in same volume
7. **LCP substrate** — enables integrated antennas, saves PCB area
