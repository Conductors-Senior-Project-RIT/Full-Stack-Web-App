The `RecordRepository` provides an abstract interface for querying records that were intercepted from EOT, HOT, and DPU signals across all stations. A record repository can be instantiated by using the factory functions in [db.record_types][src.db.record_types]; however, only EOT and HOT records are accessible currently.

## Type Variables Used {#types-record}

### `RecordType` & `CollationType`
Generic type variables that are constrained to only accept types that are subclasses of [`BaseRecord`][src.db.db_core.models.BaseRecord] and [`CollationMixin`][src.db.db_core.models.CollationMixin], respectively. Provides type safety by rejecting incompatible types at runtime.

::: src.db.record_repo