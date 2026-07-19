"""DSC message validator per ITU-R M.493-16."""

from __future__ import annotations

from ..protocol.message import DSCMessage
from ..protocol.error_correction import compute_ecc, verify_ecc
from ..protocol.symbols import SYM_DISTRESS, SYM_CAT_DISTRESS


class DSCValidator:
    """Validate DSC messages for correctness per ITU-R M.493-16."""

    def validate(self, msg: DSCMessage) -> tuple[bool, list[str]]:
        """Validate a DSC message."""
        errors = []

        if msg.format_specifier is None:
            errors.append("Missing format specifier")

        # Valid format specifiers
        valid_formats = {112, 116, 114, 120, 102, 123}
        if msg.format_specifier is not None and msg.format_specifier not in valid_formats:
            errors.append(f"Invalid format specifier: {msg.format_specifier}")

        # Valid categories
        valid_categories = {100, 108, 110, 112}
        if msg.category is not None and msg.category not in valid_categories:
            errors.append(f"Invalid category: {msg.category}")

        # MMSI validation
        if msg.mmsi_self and len(msg.mmsi_self) != 9:
            errors.append(f"Invalid MMSI self length: {len(msg.mmsi_self)}")
        if msg.mmsi_dest and len(msg.mmsi_dest) != 9:
            errors.append(f"Invalid MMSI dest length: {len(msg.mmsi_dest)}")

        # ECC validation (only if we have enough symbols)
        if msg.ecc is not None and msg.raw_symbols and len(msg.raw_symbols) >= 10:
            # DX stream structure: [info_symbols..., EOS, ECC, EOS]
            # ECC is computed over info_symbols + first EOS (excluding ECC and trailing EOS)
            info_symbols = msg.raw_symbols[:-2]  # Exclude ECC and trailing EOS
            expected_ecc = compute_ecc(info_symbols)
            if expected_ecc != msg.ecc:
                errors.append(f"ECC check failed: expected {expected_ecc}, got {msg.ecc}")

        if msg.is_distress and msg.nature_of_distress is None:
            errors.append("Distress message missing nature of distress")

        return len(errors) == 0, errors

    def validate_ecc(self, msg: DSCMessage) -> bool:
        """Validate only the ECC of a message."""
        if msg.ecc is None or not msg.raw_symbols:
            return False
        info_symbols = msg.raw_symbols[:-2]
        return compute_ecc(info_symbols) == msg.ecc

    def validate_structure(self, msg: DSCMessage) -> bool:
        """Validate message structure without ECC."""
        return msg.format_specifier is not None
