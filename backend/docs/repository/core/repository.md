## Type Definitions Used {#types}

### `ModelType`
A generic type variable that is constrained to only accept types that are subclasses of [`Base`][src.db.db_core.models.Base]. Provides type safety by rejecting incompatible types at runtime.

**Bound To**: [`Base`][src.db.db_core.models.Base]

### `SingleResult`
A return type that can either be a `ModelType` or `dict` instance.

**Bound To:** `dict` *or* `ModelType`

### `CollectionResult`
A return type that can be a list of `ModelType` or `dict` instances.

**Bound To:** `list[ModelType]` *or* `list[dict]`

::: src.db.db_core.repository