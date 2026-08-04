---
date: 2026-08-11
topic: Interface 53 Fixed-Width Parsers
status: validated
---

# Interface 53 Fixed-Width Parsers

## Problem Statement

Interface 53 reception messages need a deterministic, standalone parser for the
fixed-width records exchanged with Reflex. The parser must preserve protocol
meaning while exposing typed values to callers, without coupling parsing to an
Odoo model, processor, or stream lifecycle.

## Constraints

- The implementation belongs in `wms_reflex_connector/parser_reflex/rec53.py`.
- Only rubriques 110, 120, 130, 150, 310, and 340 are in scope; these are the
  only rubriques whose layouts are fully specified.
- Every record payload is exactly 270 characters: a 14-character common
  envelope followed by a 256-character rubrique body. A single LF or CRLF may
  terminate the payload; no other length variation is valid.
- Identifiers and codes remain strings, quantities are integers, and 9,3
  measurements are `Decimal` values using the protocol's implied decimal.
- Blank optional numeric fields become `None`. Dates and times remain strings.
  Text fields lose only their right-padding; meaningful leading or internal
  whitespace is preserved.
- Parsing is strict and errors must identify the parser and the relevant
  record/field context.
- There is no stream state and no Odoo processor integration in this design.

## Approach

Implement six standalone fixed-width reception parsers in `rec53.py`. Each
rubrique has one keyword-only dataclass and a record-owned parse entry point.
The dataclasses share a record foundation containing the common envelope and
their rubrique-specific fields. A single dispatcher reads the rubrique from
the validated envelope and invokes the matching record parser.

Parsing is deliberately positional: field slices are defined by the protocol
layout, then converted according to the field's declared type. Structural
checks happen before typed conversion so malformed records fail predictably,
and no partially valid record is returned.

## Architecture

The module is a pure protocol boundary. It accepts one complete record at a
time and returns a typed dataclass instance. The common foundation owns the
shared envelope sequence and application/interface/rubrique/activity/location/
reception-year/reception-number fields. Concrete rubrique records extend that
foundation with only the fields documented for their layout.

All record dataclasses are keyword-only, preventing accidental positional
field shifts when layouts evolve. The record-owned parse entry point is the
authoritative way to construct each record; callers do not assemble dataclass
instances from ad-hoc slices. The dispatcher is the only multi-rubrique entry
point and maps the six supported rubrique codes to their record parsers.

## Components

- **Common record foundation:** validates the 14-character envelope and
  exposes sequence, application, interface, rubrique, activity, location,
  reception year, and reception number.
- **Six keyword-only records:** one dataclass/parser each for rubriques 110,
  120, 130, 150, 310, and 340, with their complete 256-character body
  layouts.
- **Fixed-width field helpers:** centralize exact slicing, right-padding
  removal for text, integer conversion, implied-decimal `Decimal` conversion,
  and optional blank numeric handling.
- **Dispatcher:** validates the complete record, identifies its rubrique, and
  delegates to exactly one supported record parser.
- **Parser-specific error type:** a `ValueError` subtype carrying contextual
  information such as rubrique, field, offset, and offending structural or
  typed value.

## Data Flow

1. A caller supplies one 270-character record, optionally followed by one LF
   or CRLF terminator.
2. The boundary normalizes only that permitted terminator and verifies the
   exact payload length.
3. The common envelope is sliced and validated, including the rubrique code.
4. The dispatcher selects the corresponding rubrique parser.
5. The selected parser slices all fields at their protocol offsets, trims only
   right-padding from text, and converts typed values.
6. The parser returns one fully populated keyword-only dataclass, or raises a
   contextual parser-specific `ValueError` before returning anything.

No parser retains input, cursor, or cross-record state. A caller that has a
stream is responsible for framing records before invoking this boundary.

## Error Handling

Malformed structure is rejected strictly: unsupported rubrique codes, invalid
record lengths, unexpected terminators, and invalid envelope values are
errors. Typed conversion errors are likewise rejected for quantities and
measurements; an empty optional numeric slice is the sole case converted to
`None`.

All failures use the parser-specific `ValueError` subtype and include enough
context to diagnose the protocol location, at minimum the rubrique (when
known), field name or structural area, and field offset/value where relevant.
Errors do not silently coerce malformed values, discard non-padding text, or
fall back to an undocumented layout.

## Testing Strategy

Tests will exercise six representative records, one for every supported
rubrique, and assert every field's parsed value. They will also cover
dispatcher selection, keyword-only construction behavior, LF and CRLF
terminators, exact protocol boundaries, accepted/rejected lengths, envelope
headers, and unsupported rubriques.

Typed failure cases will include malformed integer and implied-decimal values,
while fixtures verify preservation of leading zeroes in identifiers/codes,
correct 9,3 decimal interpretation, blank optional numerics as `None`, and
right-padding-only text cleanup. Boundary tests will prove that no stream
state or processor integration is required.

## Open Questions

No blocking questions remain for the validated scope. Rubriques without fully
specified layouts are intentionally undocumented and deferred until their
protocol definitions are available.
