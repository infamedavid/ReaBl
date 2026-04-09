# ReaBl Bitwig Bridge Technical Audit (2026-04-09)

This document captures a production-readiness audit of the Bitwig OSC bridge implementation.

## Scope

- `src/main/java/com/infamedavid/reablbitwig/ReaBlBitwigExtension.java`
- `src/main/java/com/infamedavid/reablbitwig/ReaBlBitwigDefinition.java`
- Build and packaging files (`build.gradle`, service declaration, README)

## High-priority findings

1. **Observer bootstrap can emit false transport events on load**
   - `isPlaying` observer can schedule stop/pause on first callback because `wasPlaying` is toggled directly from observer events.
   - A short guard around observer initialization is recommended.

2. **Stop/pause decision task is stale-prone**
   - `scheduleTask(..., 30ms)` can run after transport re-enters play, causing stale stop/pause dispatch.
   - Add a generation token or pending-task cancellation strategy.

3. **Reconnect can race with in-flight sends**
   - `closeSocket()` swaps mutable socket/address while send methods read mutable fields.
   - Snapshot socket/address/port before send and ignore stale closes.

## Recommended improvements

- Add rate-limited warning when socket is unavailable to improve observability.
- Add small helper for OSC message construction to reduce repeated allocations.
- Pin Gradle wrapper for reproducible builds; current repo depends on system Gradle.

## Compatibility note

All recommended fixes can be applied without changing OSC address names or argument types:

- `/reabl/state/time` as float
- `/reabl/transport/play` as int `1`
- `/reabl/transport/stop` as int `1`
- `/reabl/transport/pause` as int `1`
