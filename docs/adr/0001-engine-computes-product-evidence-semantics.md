# The engine computes product-level evidence semantics, not just raw synastry facts

Status: accepted

Synastry output could have stopped at raw facts (which planets form which aspect at
which orb, which planet falls in which house, which Human Design channel connects) and
left the scoring — `dimensions`, `salience`, `ease_or_tension`, `data_confidence`,
`participates_in_convergence` — to the hosted product. That would have kept this repo
matching its own stated boundary: a pure compute core, with product concerns living in
the hosted version. We decided the opposite: the engine emits complete Evidence objects,
including the product-defined `themes-v1` ontology.

The reason is that the scoring rules are arithmetic over the numbers computed here, and
nothing else. `salience` is `orb_weight × planet_weight` where `orb_weight` is
`max(0, 1 - (orb / max_orb)²)`; `dimensions` is a table lookup on the same planets the
aspect was computed from; `data_confidence` depends on whether birth time was known,
which is an input to this engine. Splitting the formula from its inputs would mean
shipping the orb, the max orb, the weights and the time-certainty flags across an HTTP
boundary so a second codebase could multiply them — with the determinism guarantee, the
golden fixtures and the mutation tests all on the wrong side of that boundary. Keeping
them together is what makes a wrong `salience` a failing test here rather than a silent
product defect there.

## Consequences

- This repo now carries an ontology that is **not** native to any divination tradition.
  `themes-v1`'s ten IDs are a product invention. A reader must not mistake them for
  astrological or Human Design canon; they are labelled as product-level in `CONTEXT.md`
  and in the theme tables themselves.
- The ontology is duplicated: this repo and the hosted product each hold a copy of the
  `themes-v1` constant, and a checked-in comparison test asserts they are character-for-
  character identical. A change here is a breaking change there.
- The exception is bounded to scoring and theme mapping. Accounts, payments, analytics,
  prompt text and LLM calls remain out of this repo, unchanged.
- Reversing this later means moving the formulas to the consumer and re-verifying every
  consumer path that reads Evidence — meaningful, not catastrophic, but not a refactor
  either.
