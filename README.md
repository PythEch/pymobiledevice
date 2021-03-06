What is this?
------------------

Jython port of [pymobiledevice](https://github.com/GotoHack/pymobiledevice)

pymobiledevice is a python implementation of the libimobiledevice cross-platform software library that talks the protocols to support iPhone®, iPod Touch®, iPad® and Apple TV® devices.

The purpose of this fork is to create a _usable_ Java library for communicating with iDevices.

The idea originally came from [Taconut](https://github.com/Triforce1), which later became a side-project of [Icew1nd](https://github.com/Triforce1/Icew1nd/).

If you want to use this in Java, [JMobileDevice](https://github.com/Triforce1/JMobileDevice) can handle the wrapper part for you.

Why create yet another library?
------------------

Generally it's a better practice to follow [C libimobiledevice](https://github.com/libimobiledevice/libimobiledevice) which is actively developed.

But for some reason, I guess because of licensing problems, [libimobiledevice-wrapper](https://github.com/ios-driver/libimobiledevice-wrapper) depends on [libimobiledevice-sdk (LGPL 2.1)](http://cgit.sukimashita.com/libimobiledevice-sdk.git/) which is not available to the public, making it impossible to use unless someone writes a libimobiledevice-sdk alternative.
