---
date: 2026-08-11
topic: Interface 62 GEI Movement Parsers
status: validated
---

# Interface 62 GEI Movement Parsers

## Problem Statement

Interface 62 GEI movement messages need a deterministic fixed-width parser that
exposes the fields required by the validated protocol without coupling syntax
parsing to Odoo models or business processing. The design is intentionally
limited to the two specified movement rubriques: 110 and 112.

## Constraints

- The source of truth for rubrique scope is `HL62_MOUVEMENT GEI.docx`; field
  positions are based on the byte-identical `Int62-Mouvement de GEI.xls`.
- Rubrique 110 exposes only its 12 highlighted fields. Rubrique 112 exposes
  only creation date, in addition to the common envelope.
- Rubriques 010 and 111 are explicitly out of scope and must not be
  implemented from the workbook.
- A physical record is exactly 270 characters: sequence positions 1-7, HL
  positions 8-9, interface 62 positions 10-11, rubrique positions 12-14, and
  a 256-character body at positions 15-270. Exactly one LF or CRLF may follow
  the record.
- Sequence is an integer. Identifiers and codes are strings with only
  right-space padding removed, preserving leading zeroes. Quantity is an
  optional integer, and creation date is an eight-ASCII-digit `SSAAMMJJ`
  string.
- Structural validation is exact for envelope, length, and permitted
  terminators. Only trailing reserved padding is required to contain spaces;
  ignored intermediate fields are not required to be spaces.
- Syntax parsing does not apply business filters or Odoo-dependent behavior.

## Approach

Use direct positional parsing of one complete record at a time. Validate the
physical envelope and body length first, dispatch on the rubrique, then slice
only the documented fields at their fixed positions and convert them to their
declared types. Use one keyword-only base dataclass for shared envelope data and
two concrete keyword-only dataclasses for rubriques 110 and 112. Parsing errors
use a contextual `ValueError` subtype.

## Architecture

The parser is a pure protocol boundary. A common base record owns the sequence,
HL value, interface, and rubrique envelope values. `Rubrique110` adds the 12
highlighted movement fields, while `Rubrique112` adds only creation date. A
dispatcher validates the common record framing, identifies 110 or 112, and
invokes the corresponding direct parser. No parser retains stream or
cross-record state.

## Components

- **Common envelope/base dataclass:** keyword-only fields for sequence, HL,
  interface 62, and rubrique, with exact envelope validation.
- **Rubrique 110 parser/dataclass:** physical location, movement year, movement
  number, movement direction, stock type, GEI movement type, stock movement
  type, stock movement reference, miscellaneous reason, article, quality, and
  optional movement quantity base VL.
- **Rubrique 112 parser/dataclass:** creation date plus the common envelope.
- **Dispatcher:** selects only rubrique 110 or 112 and rejects unsupported
  rubrique values.
- **Contextual parser error:** a `ValueError` subtype identifying the rubrique,
  field or structural area, and relevant value/position where applicable.

The rubrique 110 body positions are: physical location body 1-3/full 15-17;
movement year body 7-8/full 21-22; movement number body 9-17/full 23-31;
movement direction body 18/full 32; stock type body 19-21/full 33-35; GEI
movement type body 22-24/full 36-38; stock movement type body 25-27/full
39-41; stock movement reference body 41-60/full 55-74; miscellaneous reason
body 61-63/full 75-77; article body 132-147/full 146-161; quality body
153-155/full 167-169; and movement quantity base VL body 156-164/full
170-178.

The rubrique 112 creation date is body 162-169/full 176-183. Its remaining
body positions are ignored except for trailing reserved padding at body
196-256/full 210-270. Rubrique 110 requires trailing reserved padding at body
234-256/full 248-270.

## Data Flow

1. Receive one 270-character physical record, optionally followed by LF or
   CRLF.
2. Remove only that permitted terminator and reject any other length or
   terminator form.
3. Validate sequence, HL, interface 62, and rubrique envelope positions.
4. Dispatch rubrique 110 or 112.
5. Slice the documented body positions directly; right-trim only spaces from
   string identifiers/codes, preserve leading zeroes, and convert sequence and
   quantity as specified.
6. Validate only the applicable trailing reserved padding and return the
   keyword-only dataclass.

## Error Handling

Reject invalid physical lengths, unexpected terminators, malformed envelope
values, unsupported rubriques, invalid sequence or quantity values, and an
invalid creation-date shape. Blank movement quantity is the sole optional
numeric case and becomes `None`. All failures raise the contextual parser
`ValueError` subtype and include the relevant rubrique plus field or structural
location. Ignored intermediate bytes are not rejected merely because they are
non-space.

## Business Filtering

Business interpretation remains outside the syntax parser. In particular, the
miscellaneous reason filter (reason begins with `*`) and table-5
transcodification are applied by the consuming business layer, not by record
parsing. The parser returns the preserved reason/code values and performs no
Odoo lookup or movement-selection policy.

## Testing Strategy

Tests cover representative valid records for rubriques 110 and 112 and assert
all exposed fields, exact offsets, leading-zero preservation, right-space
trimming, optional quantity handling, and the eight-digit creation date. They
also cover dispatcher selection, keyword-only dataclass construction, LF and
CRLF acceptance, exact 270-character framing, envelope validation, trailing
reserved padding, unsupported rubriques, and contextual conversion failures.
Fixtures deliberately use non-space values in ignored intermediate fields to
prove they are not over-validated. Tests have been added as part of the
validated change, but no Odoo-dependent test execution is available locally.

## Open Questions

No blockers remain. Rubriques 010 and 111, and any other layouts not specified
by the validated Interface 62 documentation, are deferred and must not be
inferred from the workbook.
