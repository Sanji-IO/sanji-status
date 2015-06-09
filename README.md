sanji-status
============

This bundle provides system-status related interfaces.

## Build

```
make archive
make -C build-deb
```

## Commit Changes

Whenever a set of changes are ready to be committed, you should:

1. Update `version` in `bundle.json`.
2. Use `make -C build-deb changelog` to add change-logs.
