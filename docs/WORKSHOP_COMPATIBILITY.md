# Workshop compatibility

The following directories are ordered curriculum consumed by an external workshop:

- [`python/01-learn/`](../python/01-learn/)
- [`typescript/01-learn/`](../typescript/01-learn/)

They are not ordinary end-to-end application examples. This repository cleanup preserves both source trees byte-for-byte and keeps their version-1 `samples.json` categories and records field-for-field and in order.

## Compatibility rules

Without a coordinated workshop release:

- Do not move, rename, renumber, consolidate, or delete either tree or an existing lesson.
- Do not change importer-visible file names, notebook names, or relative links.
- Do not remove or rewrite the existing workshop records in `samples.json`.
- Keep lesson ordering and entry-point conventions stable.

The `Samples manifest` workflow rejects ordinary pull requests that alter protected content. A maintainer may apply the `workshop-compatible-change` label only after the workshop owner has reviewed the change and downstream verification is planned.

Security fixes may be applied when necessary, but the workshop owner must be notified and the importer must be reverified.

## Future contract

A future change may replace path-based discovery with a versioned workshop manifest. That migration must be additive first: inventory the current importer, add and test the new manifest, release the workshop consumer, and remove path compatibility only in a separate reviewed change.
