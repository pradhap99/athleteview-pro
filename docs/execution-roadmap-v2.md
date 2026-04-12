# AthleteView — Founder's Execution Roadmap Data

## FOUNDER CONTEXT
- Name: Pradhap M
- Current role: AI Product Manager at Zoho Corporation
- Location: India (Tamil Nadu likely, given Zoho)
- Budget: $50-100K personal bootstrapping
- Background: IIT Madras, South Asian Games triathlon, 3+ years PM, managed 185+ engineers
- Target market: Indian cricket (IPL) first, then multi-sport

## PHASE 0: LEGAL FOUNDATION (Weeks 1-3) — Cost: ₹25,000-40,000 ($300-480)
### Week 1-2: Incorporate Private Limited Company
- Register "AthleteView Technologies Pvt Ltd" via SPICe+ form on MCA portal
- Cost: ₹12,000-30,000 (includes DSC, DIN, name reservation, stamp duty, professional fees)
- Get PAN, TAN automatically via SPICe+
- Open current account (Razorpay/HDFC/ICICI — choose one with startup banking benefits)
- Timeline: 7-15 working days from application
- Source: RegisterKaro 2026 guide

### Week 2-3: DPIIT Startup Recognition
- Apply via Startup India portal → NSWS website
- AthleteView qualifies as Deep Tech Startup (hardware + AI = extended to 20 years recognition, ₹300cr turnover threshold per Feb 2026 DPIIT revision)
- Benefits: 3-year tax holiday (80IAC), self-certification under labor/environment laws, public procurement relaxation, Fund of Funds access
- Timeline: 7-15 working days after submission
- Cost: FREE
- Source: DPIIT Feb 2026 notification, ClearTax guide

### Week 2: GST Registration
- Mandatory for selling goods
- Cost: Free (government) + ₹2,000-5,000 (professional)

### Week 3: MSME/Udyam Registration
- Free online registration
- Benefits: Priority sector lending, government tender eligibility, subsidy access

## PHASE 1: PROOF OF CONCEPT (Weeks 1-8) — Cost: $3,000-5,000
### Goal: Working hardware prototype that proves the concept

### Week 1-4: Development Board Prototyping
- Order LuckFox Pico Ultra (RV1106 dev board) — $20 each, order 3
- Order Arducam IMX415 camera module — $25 each, order 2
- Order MAX86178 evaluation kit (Analog Devices MAXREFDES104) — $100
- Order ICM-45686 evaluation board (TDK) — $50
- Order nRF54L15 DK (Nordic) — $40
- Order CYW55913 evaluation kit (Infineon) — $80
- Total dev kit cost: ~$500-700
- Source: LCSC, Mouser India, DigiKey, direct from manufacturers

### Week 2-6: Software Integration on Dev Boards
- Port YOLO26 to RKNN format for RV1106 NPU
- Test camera pipeline: IMX415 → MIPI → RV1106 ISP → H.265 encode
- Test biometric data acquisition: MAX86178 PPG+ECG via I2C
- Test IMU data: ICM-45686 via SPI
- Test BLE connectivity: nRF54L15 → smartphone app
- Already have working demo pipeline (300 frames tested) — extend to hardware

### Week 4-8: Integration Testing
- Wire all dev boards together on breadboard
- Validate end-to-end: camera capture → on-device YOLO inference → BLE streaming → phone display
- Validate biometric pipeline: PPG → HR/SpO2 → BLE → phone
- Document everything — this becomes your demo for investors/grants
- Film demo videos for pitch

## PHASE 2: CUSTOM PCB PROTOTYPE (Weeks 6-16) — Cost: $5,000-10,000
### Goal: First custom PCB that fits in patch form factor

### Week 6-8: Schematic Design
- Hire freelance hardware engineer (Upwork/Toptal) — $2,000-4,000 for schematic + layout
- OR engage EMS partner (Kaynes/SFO) for design services
- Design 8-layer LCP rigid-flex schematic with all v3.0 components
- Review BOM, verify all component footprints

### Week 8-10: PCB Layout
- Route 8-layer rigid-flex in KiCad/Altium
- Antenna design for WiFi 6E, BLE 6.0, UWB, 5G (critical — needs RF engineer)
- Design review with manufacturer (JLCPCB flex or PCBWay)
- DFM (Design for Manufacturability) check

### Week 10-12: PCB Fabrication
- Order 5-10 prototype PCBs from JLCPCB/PCBWay
- 8-layer rigid-flex: $100-300 per board for prototype quantities
- Lead time: 7-15 business days fabrication + 5-7 days shipping
- Total: ~$1,500-3,000 for PCBs

### Week 12-14: Component Sourcing & Assembly
- Source all components (LCSC, Mouser India, Element14)
- Component cost: ~$82/unit × 5 prototypes = $410
- Assembly: hand-solder or JLCPCB SMT assembly (~$30-50/board)
- Total: ~$800-1,200

### Week 14-16: Prototype Testing
- Power-on testing, component verification
- Camera image quality validation
- Biometric sensor calibration
- Wireless range testing (WiFi, BLE, UWB)
- Battery life measurement
- Waterproofing test (ALD + Parylene — send to coating service)
- Bug fixes, prepare for EVT

## PHASE 3: GRANT APPLICATIONS & INCUBATION (Weeks 8-20) — Cost: $0 (free applications)
### Apply in parallel with Phase 2

### NIDHI-PRAYAS (Priority #1)
- Grant: Up to ₹10 lakhs ($12,000) for prototype development
- Duration: 18 months
- Apply through nearest PRAYAS Centre (IIT Madras IITM Incubation Cell — closest to founder)
- Requirement: Physical product prototype (AthleteView qualifies perfectly)
- Need: NOC from Zoho (if still employed), business plan, proof of concept
- Selection: Expert committee at TBI → PMC approval
- Source: nidhi-prayas.org, KIIT TBI guide

### NIDHI-SSS (Seed Support System)
- Grant: Up to ₹50 lakhs ($60,000) — for startups post-prototype
- Apply after PRAYAS or in parallel if prototype exists
- Through same TBI/STEP ecosystem

### Startup India Seed Fund Scheme (SISFS)
- Grant: Up to ₹50 lakhs ($60,000)
- For concept validation, prototype development, product trials, market entry
- Apply through incubator

### iDEX (Defence Innovation)
- If sports wearable has dual-use (military fitness monitoring)
- Grant: Up to ₹1.5 crores ($180,000)
- Worth exploring for athlete monitoring → soldier monitoring angle

### BioNEST / BIRAC
- If positioning health monitoring angle
- Grants up to ₹50 lakhs for biotech/medtech startups

## PHASE 4: EVT (Engineering Validation Test) (Weeks 16-24) — Cost: $8,000-15,000
### Goal: 10-20 units that work reliably

### Week 16-18: PCB Rev 2
- Fix all issues found in Phase 2 prototype
- Optimize power routing, antenna tuning
- Order 20 PCBs: ~$2,000-3,000
- Assembly: SMT via JLCPCB or local EMS: ~$1,500-2,500

### Week 18-20: Housing Design
- 3D design of silicone/TPU housing (72×48×4.5mm)
- Prototype via 3D printing (SLA resin) — $200-500 for 20 units
- Design camera lens window, adhesive layer
- Source medical-grade adhesive (3M/Lohmann samples — free for prototyping)

### Week 20-22: System Integration
- Assemble complete units: PCB + battery + housing + adhesive
- Flash firmware, calibrate sensors
- Full system test: 4K capture + biometrics + wireless + AI inference
- Battery life validation (target: 3.5-4 hours)

### Week 22-24: Field Testing
- Test on actual athletes (cricket players)
- Contact local cricket academies, Ranji Trophy players
- Test in match conditions: sweat, impact, outdoor lighting
- Record demo footage for investors
- Collect performance data

## PHASE 5: MARKET VALIDATION & PILOT (Weeks 20-32) — Cost: $5,000-10,000
### Goal: Prove market demand with real customers

### Week 20-24: IPL Ecosystem Outreach
- Contact IPL franchise analytics departments (Mumbai Indians, CSK, RCB have known tech teams)
- Leverage IIT Madras alumni network (several IPL team owners/management have IITM connections)
- Offer FREE pilot: 5 patches per team for training analysis
- India sports tech market: $442M in 2024, growing at 13.32% CAGR to $1.48B by 2033 (IMARC)
- IPL teams already use Catapult GPS vests — AthleteView is the upgrade

### Week 24-28: Academy Partnerships
- Target 3-5 cricket academies (MRF Pace Academy, BCCI NCA, state academies)
- Offer subsidized pricing for data partnership
- Use their athletes for extended field testing

### Week 28-32: First Revenue
- Sell pilot packages: 10 patches + cloud dashboard + analytics
- Pricing: $499/patch retail, $3,500 for team package (10 patches + 1 year cloud)
- Target: 3-5 paying customers by end of this phase
- Revenue: $10,000-17,500

## PHASE 6: DVT + CERTIFICATION (Weeks 24-36) — Cost: $15,000-25,000
### Goal: Production-ready design, all certifications

### Week 24-28: DVT (Design Validation Test)
- 50 units production run via EMS partner
- Full environmental testing: thermal cycling, drop test, sweat immersion, IP68 verification
- Battery safety testing (UN 38.3 for LiPo)
- EMC pre-scan

### Week 28-36: Certifications
- BIS CRS Registration: ₹50,000-1,50,000 ($600-1,800), 20-30 working days
- WPC Approval (wireless): ₹25,000-75,000 ($300-900), for WiFi/BLE/5G/UWB radios
- FCC (if US market): $5,000-15,000
- CE RED (if EU market): $5,000-10,000
- FiRa UWB certification: $3,000-5,000
- Bluetooth SIG: $8,000 annual membership + testing
- Total India-only: ~$3,000-5,000
- Total with international: ~$20,000-45,000

## PHASE 7: PVT + PRODUCTION (Weeks 32-44) — Cost: $20,000-40,000
### Goal: 100-unit initial production run

### Week 32-36: PVT (Production Validation Test)
- Partner with EMS: Optiemus (Noida), Kaynes (Mysuru), or SFO (Kochi)
- 100-unit pilot run
- All-in cost: ~$220/unit × 100 = $22,000
- Yield validation, quality inspection
- Packaging design and production

### Week 36-40: Production & QC
- 100 units assembled, tested, packaged
- Individual unit testing (power-on, sensor calibration, wireless check, IP68 seal verify)
- Serial number assignment, firmware flashing
- Cloud platform ready (dashboard, API, mobile app)

### Week 40-44: Ship to Customers
- Fulfill pilot orders
- Begin ongoing sales
- Collect feedback for v3.1 iteration

## TOTAL BUDGET BREAKDOWN (Bootstrapping: $50-100K)

| Phase | Timeline | Cost (USD) | Cumulative |
|-------|----------|-----------|------------|
| Phase 0: Legal | Weeks 1-3 | $500 | $500 |
| Phase 1: PoC | Weeks 1-8 | $4,000 | $4,500 |
| Phase 2: Custom PCB | Weeks 6-16 | $8,000 | $12,500 |
| Phase 3: Grants | Weeks 8-20 | $0 (apply) | $12,500 |
| Phase 4: EVT | Weeks 16-24 | $12,000 | $24,500 |
| Phase 5: Market | Weeks 20-32 | $8,000 | $32,500 |
| Phase 6: Certification | Weeks 24-36 | $20,000 | $52,500 |
| Phase 7: Production | Weeks 32-44 | $30,000 | $82,500 |
| TOTAL | ~11 months | $82,500 | |

Buffer: $17,500 remaining from $100K for unexpected costs

Grant income (if approved): +$12,000-72,000 (PRAYAS + SISFS)

## KEY DECISION POINTS

### Decision 1 (Week 8): Continue or Pivot?
- Does the PoC work? Can RV1106G3 run YOLO26 at acceptable FPS?
- Is the camera quality good enough for sports analysis?
- If NO → pivot to software-only (use existing stadium cameras + cloud AI)

### Decision 2 (Week 16): Self-fund or Raise?
- Do you have a working prototype?
- Grant applications status?
- If prototype works + grant pending → continue bootstrapping
- If prototype works + no grant → consider angel round ($200-500K)

### Decision 3 (Week 24): Scale or Iterate?
- Field test results: do athletes/coaches want this?
- If YES → proceed to certification + production
- If MIXED → iterate on form factor, features, placement

### Decision 4 (Week 32): India-only or International?
- If India demand strong → BIS only, save $20-30K on FCC/CE
- If international interest → invest in FCC/CE certification

## CRITICAL PATH (What Blocks Everything)

1. RV1106G3 availability — verify stock at LCSC/Arrow before starting
2. MAX86178 sampling — may need to contact Analog Devices directly
3. RG255C-GL (5G RedCap) — relatively new, verify availability
4. QM35825 (UWB) — released March 2025, should be available
5. RF engineer for antenna design — this is the hardest hire
6. BIS CRS certification — cannot sell in India without it
7. Medical device classification — if making health claims (ECG/SpO2), needs CDSCO approval → adds 6-12 months. Recommendation: launch as "sports analytics device" NOT medical device initially.

## WHAT TO DO THIS WEEK (Week 0)

### Day 1-2:
- Register company name on MCA portal
- Order DSC (Digital Signature Certificate) for directors
- Create Startup India portal account

### Day 3-4:
- Order development boards (LuckFox, Arducam, Nordic DK, MAX86178 eval kit)
- Set up hardware development workspace
- Create component sourcing spreadsheet

### Day 5-7:
- Begin DPIIT application
- Apply to IIT Madras Incubation Cell for NIDHI-PRAYAS
- Start porting YOLO26 to RKNN format
- Contact Analog Devices for MAX86178 engineering samples
