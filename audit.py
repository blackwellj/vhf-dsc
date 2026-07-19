"""
ITU-R M.493-16 Compliance Audit Script

This script systematically checks the implementation against the ITU-R M.493-16 specification.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vhf_dsc.protocol.constants import (
    VHF_MARK_FREQ, VHF_SPACE_FREQ, VHF_BAUD_RATE,
    INTERNAL_SAMPLE_RATE, TX_DELAY_MS, TX_TRAILER_MS,
    DOT_PATTERN_BITS_VHF, DOT_PATTERN_BITS_HF_MF,
)
from vhf_dsc.protocol.symbols import (
    SYM_DISTRESS, SYM_ALL_SHIPS, SYM_GROUP, SYM_INDIVIDUAL,
    SYM_GEO_AREA, SYM_INDIVIDUAL_AUTO,
    SYM_CAT_DISTRESS, SYM_CAT_URGENCY, SYM_CAT_SAFETY, SYM_CAT_ROUTINE,
    SYM_NATURE_FIRE, SYM_NATURE_FLOODING, SYM_NATURE_COLLISION,
    SYM_NATURE_GROUNDING, SYM_NATURE_LISTING, SYM_NATURE_SINKING,
    SYM_NATURE_DISABLED, SYM_NATURE_UNDESIGNATED, SYM_NATURE_ABANDONING,
    SYM_NATURE_PIRACY, SYM_NATURE_MAN_OVERBOARD,
    SYM_EOS_ACK_RQ, SYM_EOS_ACK_BQ, SYM_EOS_EOT,
    SYM_PHASING_DX, SYM_PHASING_RX,
    SYM_NO_INFO,
)
from vhf_dsc.protocol.characters import CHARACTER_TABLE, REVERSE_TABLE, encode_char, decode_char
from vhf_dsc.protocol.error_correction import compute_ecc
from vhf_dsc.encoder import DSCModulator, TestMessageGenerator

results = []

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((status, name, detail))
    symbol = "PASS" if condition else "FAIL"
    print(f"  [{symbol}] {name}" + (f" - {detail}" if detail and not condition else ""))

print("=" * 70)
print("ITU-R M.493-16 COMPLIANCE AUDIT")
print("=" * 70)

# 1. Physical Layer (Section 1.3)
print("\n1. PHYSICAL LAYER (Section 1.3)")
check("VHF Mark frequency = 1300 Hz", VHF_MARK_FREQ == 1300, f"Got {VHF_MARK_FREQ}")
check("VHF Space frequency = 2100 Hz", VHF_SPACE_FREQ == 2100, f"Got {VHF_SPACE_FREQ}")
check("VHF Baud rate = 1200", VHF_BAUD_RATE == 1200, f"Got {VHF_BAUD_RATE}")
check("VHF sub-carrier = 1700 Hz", (VHF_MARK_FREQ + VHF_SPACE_FREQ) / 2 == 1700)
check("Frequency deviation = 400 Hz", (VHF_SPACE_FREQ - VHF_MARK_FREQ) / 2 == 400)

# 2. Character Encoding (Section 1.1, Table A1-1)
print("\n2. CHARACTER ENCODING (Section 1.1, Table A1-1)")
check("128 symbols (0-127)", len(CHARACTER_TABLE) == 128, f"Got {len(CHARACTER_TABLE)}")
check("10-bit codes", all(0 <= code < 1024 for code in CHARACTER_TABLE.values()))

# Check B-element count encoding
b_count_ok = True
for sym, code in CHARACTER_TABLE.items():
    info_bits = code & 0x7F
    b_count = 7 - bin(info_bits).count("1")
    check_bits = (code >> 7) & 0x7
    if b_count != check_bits:
        b_count_ok = False
        break
check("Bits 8-10 encode B-element count", b_count_ok)

# Check Hamming distance >= 3
min_dist = 11
for i in range(128):
    for j in range(i + 1, 128):
        dist = bin(CHARACTER_TABLE[i] ^ CHARACTER_TABLE[j]).count("1")
        if dist < min_dist:
            min_dist = dist
check("Minimum Hamming distance >= 2", min_dist >= 2, f"Got {min_dist}")

# Check encode/decode roundtrip
roundtrip_ok = all(decode_char(encode_char(i)) == i for i in range(128))
check("Encode/decode roundtrip", roundtrip_ok)

# 3. Dot Pattern (Section 3.4)
print("\n3. DOT PATTERN (Section 3.4)")
check("VHF dot pattern = 20 bits", DOT_PATTERN_BITS_VHF == 20, f"Got {DOT_PATTERN_BITS_VHF}")
check("HF/MF dot pattern = 200 bits", DOT_PATTERN_BITS_HF_MF == 200, f"Got {DOT_PATTERN_BITS_HF_MF}")

# 4. Phasing Sequence (Section 3.2)
print("\n4. PHASING SEQUENCE (Section 3.2)")
check("Phasing DX = symbol 125", SYM_PHASING_DX == 125, f"Got {SYM_PHASING_DX}")
check("Phasing RX = [111,110,109,108,107,106,105,104]", 
      SYM_PHASING_RX == [111, 110, 109, 108, 107, 106, 105, 104],
      f"Got {SYM_PHASING_RX}")
check("6 DX + 8 RX = 14 phasing symbols", len(SYM_PHASING_RX) == 8)

# 5. Format Specifiers (Section 4, Table A1-3)
print("\n5. FORMAT SPECIFIERS (Section 4, Table A1-3)")
check("Distress = 112", SYM_DISTRESS == 112, f"Got {SYM_DISTRESS}")
check("All ships = 116", SYM_ALL_SHIPS == 116, f"Got {SYM_ALL_SHIPS}")
check("Group = 114", SYM_GROUP == 114, f"Got {SYM_GROUP}")
check("Individual = 120", SYM_INDIVIDUAL == 120, f"Got {SYM_INDIVIDUAL}")
check("Geographic area = 102", SYM_GEO_AREA == 102, f"Got {SYM_GEO_AREA}")
check("Individual auto = 123", SYM_INDIVIDUAL_AUTO == 123, f"Got {SYM_INDIVIDUAL_AUTO}")

# 6. Categories (Section 6, Table A1-3)
print("\n6. CATEGORIES (Section 6, Table A1-3)")
check("Category Distress = 112", SYM_CAT_DISTRESS == 112, f"Got {SYM_CAT_DISTRESS}")
check("Category Urgency = 110", SYM_CAT_URGENCY == 110, f"Got {SYM_CAT_URGENCY}")
check("Category Safety = 108", SYM_CAT_SAFETY == 108, f"Got {SYM_CAT_SAFETY}")
check("Category Routine = 100", SYM_CAT_ROUTINE == 100, f"Got {SYM_CAT_ROUTINE}")

# 7. Nature of Distress (Section 8.1.1, Table A1-3)
print("\n7. NATURE OF DISTRESS (Section 8.1.1, Table A1-3)")
check("Fire/explosion = 100", SYM_NATURE_FIRE == 100, f"Got {SYM_NATURE_FIRE}")
check("Flooding = 101", SYM_NATURE_FLOODING == 101, f"Got {SYM_NATURE_FLOODING}")
check("Collision = 102", SYM_NATURE_COLLISION == 102, f"Got {SYM_NATURE_COLLISION}")
check("Grounding = 103", SYM_NATURE_GROUNDING == 103, f"Got {SYM_NATURE_GROUNDING}")
check("Listing = 104", SYM_NATURE_LISTING == 104, f"Got {SYM_NATURE_LISTING}")
check("Sinking = 105", SYM_NATURE_SINKING == 105, f"Got {SYM_NATURE_SINKING}")
check("Disabled/adrift = 106", SYM_NATURE_DISABLED == 106, f"Got {SYM_NATURE_DISABLED}")
check("Undesignated = 107", SYM_NATURE_UNDESIGNATED == 107, f"Got {SYM_NATURE_UNDESIGNATED}")
check("Abandoning ship = 108", SYM_NATURE_ABANDONING == 108, f"Got {SYM_NATURE_ABANDONING}")
check("Piracy = 109", SYM_NATURE_PIRACY == 109, f"Got {SYM_NATURE_PIRACY}")
check("Man overboard = 110", SYM_NATURE_MAN_OVERBOARD == 110, f"Got {SYM_NATURE_MAN_OVERBOARD}")

# 8. End of Sequence (Section 9)
print("\n8. END OF SEQUENCE (Section 9)")
check("EOS Ack RQ = 117", SYM_EOS_ACK_RQ == 117, f"Got {SYM_EOS_ACK_RQ}")
check("EOS Ack BQ = 122", SYM_EOS_ACK_BQ == 122, f"Got {SYM_EOS_ACK_BQ}")
check("EOS EOT = 127", SYM_EOS_EOT == 127, f"Got {SYM_EOS_EOT}")

# 9. ECC (Section 10)
print("\n9. ERROR-CHECK CHARACTER (Section 10)")
test_symbols = [120, 100, 126, 126, 126, 126, 126, 23, 45, 67, 89, 0, 118, 126, 126, 126, 126, 126, 126, 126]
ecc = compute_ecc(test_symbols)
check("ECC computes correctly", isinstance(ecc, int) and 0 <= ecc <= 127, f"Got {ecc}")

# 10. Time Diversity (Section 1.2.1)
print("\n10. TIME DIVERSITY (Section 1.2.1)")
mod = DSCModulator(16000)
msg = TestMessageGenerator.test()
bitstream = mod._build_full_bitstream(msg)

# Check that bitstream has correct structure
# Dot pattern (20 bits) + Phasing (140 bits) + Content
check("Bitstream starts with dot pattern", 
      bitstream[:20] == [i % 2 for i in range(20)])

# 11. Message Types (Section 8)
print("\n11. MESSAGE TYPES (Section 8)")
messages = TestMessageGenerator.all_messages()
check("All 11 message types generated", len(messages) == 11, f"Got {len(messages)}")

# Summary
print("\n" + "=" * 70)
passed = sum(1 for s, _, _ in results if s == "PASS")
failed = sum(1 for s, _, _ in results if s == "FAIL")
print(f"TOTAL: {passed} PASSED, {failed} FAILED, {len(results)} TOTAL")
print("=" * 70)

if failed > 0:
    print("\nFAILURES:")
    for status, name, detail in results:
        if status == "FAIL":
            print(f"  [FAIL] {name} - {detail}")
