package com.infamedavid.reablbitwig;

import java.util.UUID;

import com.bitwig.extension.api.PlatformType;
import com.bitwig.extension.controller.AutoDetectionMidiPortNamesList;
import com.bitwig.extension.controller.ControllerExtension;
import com.bitwig.extension.controller.ControllerExtensionDefinition;
import com.bitwig.extension.controller.api.ControllerHost;

public class ReaBlBitwigDefinition extends ControllerExtensionDefinition
{
    private static final UUID EXTENSION_ID = UUID.fromString("5f61cf9d-d78e-4f9e-96da-5d2a7b7a4c11");

    @Override
    public String getName()
    {
        return "ReaBl Bitwig Bridge";
    }

    @Override
    public String getAuthor()
    {
        return "ReaBl";
    }

    @Override
    public String getVersion()
    {
        return "0.3.0";
    }

    @Override
    public UUID getId()
    {
        return EXTENSION_ID;
    }

    @Override
    public int getRequiredAPIVersion()
    {
        return 25;
    }

    @Override
    public String getHardwareVendor()
    {
        return "ReaBl";
    }

    @Override
    public String getHardwareModel()
    {
        return "ReaBl Bitwig Bridge";
    }

    @Override
    public int getNumMidiInPorts()
    {
        return 0;
    }

    @Override
    public int getNumMidiOutPorts()
    {
        return 0;
    }

    @Override
    public void listAutoDetectionMidiPortNames(
        final AutoDetectionMidiPortNamesList list,
        final PlatformType platformType)
    {
        // No MIDI ports needed.
    }

    @Override
    public ControllerExtension createInstance(final ControllerHost host)
    {
        return new ReaBlBitwigExtension(this, host);
    }
}
