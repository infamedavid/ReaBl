# ReaBl Bitwig Bridge

Minimal Bitwig -> ReaBL OSC bridge.

This project does not modify the Blender add-on. It emits the same OSC addresses ReaBL already listens for:

- `/reabl/state/time`
- `/reabl/transport/play`
- `/reabl/transport/stop`
- `/reabl/transport/pause`

## What changed in 0.3.0

- Vendor and author now both appear as `ReaBl`
- Host and port moved into Bitwig controller settings
- Added a minimal settings UI via the controller gear icon
- Added a manual `Reconnect OSC` button in the controller settings
- Removed dependence on the external `.properties` file for normal use

## How to edit host and port in Bitwig

1. Open **Dashboard > Settings > Controllers**
2. Add or select **ReaBl Bitwig Bridge**
3. Click the **gear icon** on the controller entry
4. Edit:
   - `Host`
   - `Port`
5. Press `Reconnect` if needed

Typical values:

- Local same-machine workflow:
  - Host = `127.0.0.1`
  - Port = `9000`
- Network workflow:
  - Host = Blender machine LAN IP (example `192.168.1.50`)
  - Port = the port ReaBL is listening on in Blender

## What it does

- When Bitwig starts playing, it sends:
  - `/reabl/transport/play 1`
  - `/reabl/state/time <seconds>`
- While Bitwig keeps playing, it streams:
  - `/reabl/state/time <seconds>`
- When Bitwig leaves playback, it decides between:
  - `/reabl/transport/stop 1`
  - `/reabl/transport/pause 1`

## Current pause strategy

The bridge is conservative but still heuristic.

In `ReaBlBitwigExtension.java`, this line controls how non-playing state is reported:

```java
private static final StoppedStateMode STOPPED_STATE_MODE = StoppedStateMode.AUTO;
```

Options:

- `AUTO` -> tries to distinguish pause vs stop
- `ALWAYS_STOP` -> reports every playback exit as stop
- `ALWAYS_PAUSE` -> reports every playback exit as pause

If you want zero guessing, use `ALWAYS_STOP`.

## Build

This is a Java Bitwig controller extension project packaged as `.bwextension`.

Requirements:

- Java 21
- Gradle

Build command:

```bash
gradle build
```

Output:

```text
build/libs/ReaBlBitwig.bwextension
```

## Install

Copy the built `.bwextension` file to Bitwig's Extensions folder.

- Windows: `%USERPROFILE%\Documents\Bitwig Studio\Extensions`
- macOS: `~/Documents/Bitwig Studio/Extensions`
- Linux: `~/Bitwig Studio/Extensions`

Bitwig 4.2.5+ also supports drag and drop of a `.bwextension` file into the application window.
