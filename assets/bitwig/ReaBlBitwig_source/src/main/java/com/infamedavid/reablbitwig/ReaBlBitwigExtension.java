package com.infamedavid.reablbitwig;

import com.bitwig.extension.controller.ControllerExtension;
import com.bitwig.extension.controller.api.ControllerHost;
import com.bitwig.extension.controller.api.Transport;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;

public class ReaBlBitwigExtension extends ControllerExtension
{
    private static final String DEFAULT_REABL_HOST = "127.0.0.1";
    private static final int DEFAULT_REABL_PORT = 9000;

    private static final String SETTINGS_CATEGORY = "ReaBl Network";
    private static final int HOST_FIELD_LENGTH = 64;

    // AUTO tries to distinguish stop vs pause.
    // If you want zero guessing, change to ALWAYS_STOP.
    private enum StoppedStateMode
    {
        AUTO,
        ALWAYS_STOP,
        ALWAYS_PAUSE
    }

    private static final StoppedStateMode STOPPED_STATE_MODE = StoppedStateMode.AUTO;

    // Tolerance used to compare play-start marker vs last playing position.
    private static final double PAUSE_EPSILON_SECONDS = 0.050;

    // Small delay so Bitwig finishes updating values after leaving play state.
    private static final int STOP_DECISION_DELAY_MS = 30;

    private DatagramSocket socket;
    private InetAddress remoteAddress;
    private Transport transport;

    private volatile boolean wasPlaying = false;
    private volatile double playPositionSeconds = 0.0;
    private volatile double playStartPositionSeconds = 0.0;
    private volatile double lastPlayingPositionSeconds = 0.0;

    private String reablHost = DEFAULT_REABL_HOST;
    private int reablPort = DEFAULT_REABL_PORT;

    protected ReaBlBitwigExtension(
        final ReaBlBitwigDefinition definition,
        final ControllerHost host)
    {
        super(definition, host);
    }

    @Override
    public void init()
    {
        final ControllerHost host = getHost();

        initNetworkPreferences();
        reconnectOsc("startup");

        transport = host.createTransport();

        // Timeline in seconds.
        transport.playPositionInSeconds().addValueObserver(seconds ->
        {
            playPositionSeconds = seconds;
            if (wasPlaying)
            {
                lastPlayingPositionSeconds = seconds;
            }
            sendOscFloat("/reabl/state/time", (float) seconds);
        });

        // Play-start marker in seconds.
        transport.playStartPositionInSeconds().addValueObserver(seconds ->
        {
            playStartPositionSeconds = seconds;
        });

        // General play / not playing state.
        transport.isPlaying().addValueObserver(isPlaying ->
        {
            if (isPlaying)
            {
                wasPlaying = true;
                lastPlayingPositionSeconds = playPositionSeconds;
                sendOscInt("/reabl/transport/play", 1);
                sendOscFloat("/reabl/state/time", (float) playPositionSeconds);
                return;
            }

            // Transition from playing -> not playing.
            if (wasPlaying)
            {
                wasPlaying = false;
                final double stoppedAt = lastPlayingPositionSeconds;
                host.scheduleTask(() -> decideAndSendStoppedState(stoppedAt), STOP_DECISION_DELAY_MS);
            }
        });

        host.println("ReaBl Bitwig Bridge initialized.");
        host.println("Use the gear icon in Bitwig Controllers to edit Host / Port.");
    }

    private void initNetworkPreferences()
    {
        final ControllerHost host = getHost();
        final var preferences = host.getPreferences();

        final var hostSetting = preferences.getStringSetting(
            "Host",
            SETTINGS_CATEGORY,
            HOST_FIELD_LENGTH,
            DEFAULT_REABL_HOST
        );

        final var portSetting = preferences.getNumberSetting(
            "Port",
            SETTINGS_CATEGORY,
            1,
            65535,
            1,
            "",
            DEFAULT_REABL_PORT
        );

        final var reconnectSetting = preferences.getSignalSetting(
            "Reconnect OSC",
            SETTINGS_CATEGORY,
            "Reconnect"
        );

        reablHost = sanitizeHost(hostSetting.get());
        reablPort = sanitizePort((int) Math.round(portSetting.getRaw()));

        hostSetting.addValueObserver(value ->
        {
            final String sanitized = sanitizeHost(value);
            if (sanitized.equals(reablHost))
            {
                return;
            }

            reablHost = sanitized;
            reconnectOsc("host changed");
        });

        portSetting.addRawValueObserver(value ->
        {
            final int sanitized = sanitizePort((int) Math.round(value));
            if (sanitized == reablPort)
            {
                return;
            }

            reablPort = sanitized;
            reconnectOsc("port changed");
        });

        reconnectSetting.addSignalObserver(() -> reconnectOsc("manual reconnect"));
    }

    private String sanitizeHost(final String value)
    {
        if (value == null)
        {
            return DEFAULT_REABL_HOST;
        }

        final String trimmed = value.trim();
        return trimmed.isEmpty() ? DEFAULT_REABL_HOST : trimmed;
    }

    private int sanitizePort(final int value)
    {
        if (value < 1 || value > 65535)
        {
            return DEFAULT_REABL_PORT;
        }
        return value;
    }

    private void reconnectOsc(final String reason)
    {
        closeSocket();

        try
        {
            remoteAddress = InetAddress.getByName(reablHost);
            socket = new DatagramSocket();
            getHost().println(
                "ReaBl Bitwig Bridge OSC -> " + reablHost + ":" + reablPort +
                " (" + reason + ")"
            );
        }
        catch (Exception e)
        {
            remoteAddress = null;
            socket = null;
            getHost().println(
                "ReaBl Bitwig Bridge: failed to open OSC target " +
                reablHost + ":" + reablPort + " (" + reason + "): " + e.getMessage()
            );
        }
    }

    private void closeSocket()
    {
        if (socket != null && !socket.isClosed())
        {
            socket.close();
        }
        socket = null;
        remoteAddress = null;
    }

    private void decideAndSendStoppedState(final double stoppedAtSeconds)
    {
        // Reaffirm timeline when leaving playback.
        sendOscFloat("/reabl/state/time", (float) stoppedAtSeconds);

        switch (STOPPED_STATE_MODE)
        {
            case ALWAYS_STOP:
                sendOscInt("/reabl/transport/stop", 1);
                return;

            case ALWAYS_PAUSE:
                sendOscInt("/reabl/transport/pause", 1);
                return;

            case AUTO:
            default:
                // Heuristic:
                // if play-start marker lands where playback stopped,
                // treat it as pause; otherwise treat it as stop.
                final double delta = Math.abs(playStartPositionSeconds - stoppedAtSeconds);
                if (delta <= PAUSE_EPSILON_SECONDS)
                {
                    sendOscInt("/reabl/transport/pause", 1);
                }
                else
                {
                    sendOscInt("/reabl/transport/stop", 1);
                }
        }
    }

    private void sendOscInt(final String address, final int value)
    {
        if (socket == null || remoteAddress == null)
        {
            return;
        }

        try
        {
            byte[] packetData = buildOscIntMessage(address, value);
            DatagramPacket packet = new DatagramPacket(
                packetData,
                packetData.length,
                remoteAddress,
                reablPort
            );
            socket.send(packet);
        }
        catch (Exception e)
        {
            getHost().println("ReaBl Bitwig Bridge: failed sending int OSC: " + e.getMessage());
        }
    }

    private void sendOscFloat(final String address, final float value)
    {
        if (socket == null || remoteAddress == null)
        {
            return;
        }

        try
        {
            byte[] packetData = buildOscFloatMessage(address, value);
            DatagramPacket packet = new DatagramPacket(
                packetData,
                packetData.length,
                remoteAddress,
                reablPort
            );
            socket.send(packet);
        }
        catch (Exception e)
        {
            getHost().println("ReaBl Bitwig Bridge: failed sending float OSC: " + e.getMessage());
        }
    }

    private byte[] buildOscIntMessage(final String address, final int value)
    {
        byte[] addr = oscPaddedString(address);
        byte[] tags = oscPaddedString(",i");

        ByteBuffer valueBuf = ByteBuffer.allocate(4);
        valueBuf.order(ByteOrder.BIG_ENDIAN);
        valueBuf.putInt(value);

        ByteBuffer out = ByteBuffer.allocate(addr.length + tags.length + 4);
        out.put(addr);
        out.put(tags);
        out.put(valueBuf.array());

        return out.array();
    }

    private byte[] buildOscFloatMessage(final String address, final float value)
    {
        byte[] addr = oscPaddedString(address);
        byte[] tags = oscPaddedString(",f");

        ByteBuffer valueBuf = ByteBuffer.allocate(4);
        valueBuf.order(ByteOrder.BIG_ENDIAN);
        valueBuf.putFloat(value);

        ByteBuffer out = ByteBuffer.allocate(addr.length + tags.length + 4);
        out.put(addr);
        out.put(tags);
        out.put(valueBuf.array());

        return out.array();
    }

    private byte[] oscPaddedString(final String s)
    {
        byte[] raw = s.getBytes(StandardCharsets.UTF_8);
        int lenWithNull = raw.length + 1;
        int paddedLen = ((lenWithNull + 3) / 4) * 4;

        byte[] out = new byte[paddedLen];
        System.arraycopy(raw, 0, out, 0, raw.length);
        // Remaining bytes stay at zero, as required by OSC.
        return out;
    }

    @Override
    public void flush()
    {
        // Nothing to flush.
    }

    @Override
    public void exit()
    {
        closeSocket();
        getHost().println("ReaBl Bitwig Bridge closed.");
    }
}
