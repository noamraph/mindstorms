# Operate LEGO MINDSTORMS Inventor Hub from your computer

This module allows you to operate the LEGO mindstorms hub from
your computer. This means that instead of sending entire python
files to the hub and letting it run them, you can run the command
one after another from your computer. This allows easy experimenting
from a python shell on your computer, showing you completions and
API documentation on the way. This also allows you to use the
regular debugging facilities you're used to.

The API documentation was copied from the official
[LEGO MINDSTORMS Inventor Hub documentation](https://lego.github.io/MINDSTORMS-Robot-Inventor-hub-API/).

Managing the actual connection to the hub is using the excellent
[rshell](https://github.com/dhylands/rshell) project.

## Getting Started

Run:

```commandline
pip install mindstorms
```

Connect the hub to your computer using the USB cable, and then
run this from Python:

```python
from mindstorms import Hub
hub = Hub()
while True:
    while hub.motion.gesture() != hub.motion.TAPPED:
        pass
    hub.sound.play('/extra_files/Hello')
```

Tap the hub, and hear it say "hello".

## Notes

The only missing classes from the official API are `hub.BT_VCP`
and `hub.USB_VCP`. Adding them shouldn't be too difficult, 
I just didn't know how to test them.

I added all the methods from the official API, except for those that
contains a callback.

## License

MIT license.

Copyright (c) 2022 - Noam Raphael.

Based on the [official API docs](https://lego.github.io/MINDSTORMS-Robot-Inventor-hub-API/license.html):

```
The MIT License (MIT)

Copyright (c) 2017-2021 - LEGO System A/S - Aastvej 1, 7190 Billund, DK

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```