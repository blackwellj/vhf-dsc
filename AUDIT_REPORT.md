# ITU-R M.493-16 Compliance Audit Report

## Date: 2026-07-19
## Source: ITU-R M.493-16 (12/2023) - Official ITU Word/PDF Document

---

## FIXED ISSUES

### 1. Character Encoding Table (ITU Table A1-1) - FIXED
All 128 entries now match the ITU specification exactly.
Verified: check bits (bits 8-10) correctly encode B-count of info bits 1-7.

### 2. Symbol Values (ITU Table A1-3) - FIXED
- Format specifiers: 112=Distress, 116=All ships, 114=Group, 120=Individual, 102=Geo area, 123=Individual auto
- Categories: 112=Distress, 110=Urgency, 108=Safety, 100=Routine
- Nature of distress: 100=Fire, 101=Flooding, 102=Collision, 103=Grounding, 104=Listing, 105=Sinking, 106=Disabled, 107=Undesignated, 108=Abandoning, 109=Piracy, 110=Man overboard
- EOS: 117=Ack RQ, 122=Ack BQ, 127=EOT
- Phasing: DX=125, RX=[111,110,109,108,107,106,105,104]

### 3. ECC Algorithm - FIXED
Changed from CRC-7 to even vertical parity (XOR of all info symbol 7-bit values) per Section 10.2.

### 4. Position Encoding - FIXED
Now uses quadrant + degrees + minutes format per Section 8.1.2.
- Digit 1: quadrant (0=NE, 1=NW, 2=SE, 3=SW)
- Digits 2-3: latitude degrees, 4-5: latitude minutes
- Digits 6-8: longitude degrees, 9-10: longitude minutes

### 5. Distress Message Structure - FIXED
- No category field for distress alerts (Section 6.1)
- Self-identification uses ship's own MMSI
- Correct field order: Format + Self-ID(5) + Nature(1) + Coords(5) + Time(2) + TC1(1) + TC2(1)

### 6. MMSI Encoding - FIXED
Now uses 5 symbol-number character pairs per Section 5.2: (M,I)(D,X4)(X5,X6)(X7,X8)(X9,0)

### 7. Time Diversity - FIXED
Implemented 4-character spread between DX and RX transmissions per Section 1.2.1.

### 8. Dot Pattern and Phasing - FIXED
- VHF: 20-bit alternating dot pattern (Section 3.4.2)
- Phasing: 6 DX symbols (125) + 8 RX symbols (111-104) per Section 3.2

---

## REMAINING WORK

### 1. Decoder Pipeline - NEEDS COMPLETION
The decoder can process audio through the full pipeline but needs:
- Proper DX/RX de-interleaving with time diversity matching
- Phasing sequence detection and stripping before parsing
- Robust symbol synchronization for real-world signals

### 2. Real Signal Testing
The encoder generates ITU-compliant audio, but the decoder needs to be tested against:
- The real off-air MP3 recordings in the "Test Files" folder
- Known-good DSC test signals from commercial equipment

### 3. Full Message Type Coverage
- Distress relay messages (Table A1-4.3)
- Test calls (Table A1-4.7)
- Position request/response
- ACS automatic connection sequences

### 4. ITU-R M.541-11 Operational Procedures
- Distress alert retry timing
- Acknowledgment handling
- False alert cancellation

---

## TEST RESULTS

- Unit tests: 55/55 PASSED
- CLI self-tests: 176/176 PASSED

---

## COMPLIANCE SUMMARY

| Component | Status | Notes |
|-----------|--------|-------|
| Character encoding (Table A1-1) | COMPLIANT | All 128 entries verified |
| ECC (Section 10.2) | COMPLIANT | Even vertical parity |
| Format specifiers (Section 4) | COMPLIANT | Symbol numbers 100-127 |
| Categories (Section 6) | COMPLIANT | Symbol numbers from Table A1-3 |
| Nature of distress (Section 8.1.1) | COMPLIANT | Symbols 100-110 |
| Position encoding (Section 8.1.2) | COMPLIANT | Quadrant+deg+min |
| Time encoding (Section 8.1.3) | COMPLIANT | HHMM format |
| MMSI encoding (Section 5.2) | COMPLIANT | 5 char pairs |
| Time diversity (Section 1.2.1) | COMPLIANT | 4-char spread |
| Dot pattern (Section 3.4) | COMPLIANT | 20 bits for VHF |
| Phasing (Section 3.2) | COMPLIANT | DX=125, RX=111-104 |
| EOS (Section 9) | COMPLIANT | 117/122/127 |
| Distress structure (Table A1-4.1) | COMPLIANT | No category field |
| Individual call (Table A1-4.5) | COMPLIANT | Full structure |
| Group call (Table A1-4.6) | COMPLIANT | Full structure |
| VHF physical layer (Section 1.3.2) | COMPLIANT | 1300/2100 Hz, 1200 baud |
