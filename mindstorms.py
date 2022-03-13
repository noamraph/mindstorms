from __future__ import annotations

from typing import Optional, Union
from functools import partial

from serial.tools.list_ports import comports
from rshell.pyboard import Pyboard

USB_VID = 0x0694
USB_PID = 0x0010


def find_device():
    for port in comports():
        if port.vid == USB_VID and port.pid == USB_PID:
            return port.device
    else:
        raise RuntimeError("Couldn't find USB device")


class Hub:
    def __init__(self, device: Optional[str] = None):
        if device is None:
            device = find_device()
        self._pb = Pyboard(device)
        self._pb.enter_raw_repl()
        self._pb.exec_('import hub; Image = hub.Image; import os')

        self.battery = Battery(self, 'hub.battery')
        self.bluetooth = Bluetooth(self, 'hub.bluetooth')
        self.button = Buttons(self, 'hub.button')
        self.display = Display(self, 'hub.display')
        self.motion = Motion(self, 'hub.motion')
        self.port = Ports(self, 'hub.port')
        self.sound = Sound(self, 'hub.sound')
        self.supervision = Supervision(self, 'hub.supervision')

        self.Image = Image

        # This is not in the original hub class, but useful
        self.os = Os(self)

    def close(self):
        self._pb.close()

    def _eval(self, expr):
        b = self._pb.exec_(f'print(repr({expr}))')
        return eval(b)

    def _call(self, name, *args, **kwargs):
        parts = [repr(arg) for arg in args] + [f'{k}={v!r}' for k, v in kwargs.items()]
        expr = f"{name}({', '.join(parts)})"
        return self._eval(expr)

    def _mcall(self, name, method, *args, **kwargs):
        return self._call(f'{name}.{method}', *args, **kwargs)

    @property
    def __version__(self):
        """
        The firmware version of the form 'v1.0.06.0034-b0c335b', consisting of the components:

        v major . minor . bugfix . build - hash.
        """
        return self._eval('hub.__version__')

    @property
    def config(self):
        return self._eval('hub.config')

    def info(self):
        return self._eval('hub.info()')

    def status(self):
        """
        Gets the state of internal sensors, external devices, and the display.
        """
        return self._eval('hub.status()')

    def power_off(self, *args, **kwargs):
        """
        power_off(fast=True, restart=False) -> None
        power_off(timeout=0) -> None

        Turns the hub off, or sets a timeout to turn off after inactivity.

        Keyword Arguments:
        fast – Select True for fast shut down, without the usual light animation and sound.
        restart – Select True to reboot after shutting down.
        timeout – Sets the inactivity timeout before the hub shuts down automatically.
        """
        return self._call('hub.power_off', *args, **kwargs)

    def temperature(self) -> float:
        """
        Gets the temperature of the hub.

        Returns:
        The temperature in degrees Celsius.
        """
        return self._eval('hub.temperature()')

    def led(self, *args, **kwargs):
        """
        led(color: int) -> None
        led(red: int, green: int, blue: int) -> None
        led(color: Tuple[int, int, int]) -> None

        Sets the color of the LED in the center button of the hub.

        Parameters:
        color – Choose one of these formats:
            Color code:
            0 = off
            1 = pink
            2 = violet
            3 = blue
            4 = turquoise
            5 = light green
            6 = green
            7 = yellow
            8 = orange
            9 = red
            10 = white
            Any other value gives dim white light.

        RGB mode: You provide the intensity for red, green, and blue light separately.
        Each value must be between 0 and 255.

        Tuple mode. This works just like RGB mode, but you can provide all three values in a single tuple.
        """
        self._call('hub.led', *args, **kwargs)

    # The top of the hub. This is the side with the matrix display.
    TOP = 0

    # The front of the hub. This is the side with the USB port.
    FRONT = 1

    # The right side of the hub. This is the side with ports B, D, and F.
    RIGHT = 2

    # The bottom side of the hub. This is the side of the battery compartment.
    BOTTOM = 3

    # The back side of the hub. This is the side with the speaker.
    BACK = 4

    # The left side of the hub. This is the side with ports A, C, and E.
    LEFT = 5


# noinspection PyProtectedMember
class Battery:
    def __init__(self, hub: Hub, me: str):
        self._hub = hub
        self._me = me

    def voltage(self) -> int:
        """
        Gets the battery voltage.

        Returns:
        The voltage in in mV.
        """
        return self._hub._mcall(self._me, 'voltage')

    def current(self) -> int:
        """
        Gets current flowing out of the battery.

        Returns:
        The current in in mA.
        """
        return self._hub._mcall(self._me, 'current')

    def capacity_left(self) -> int:
        """
        Gets the remaining capacity as a percentage of a fully charged battery.

        Returns:
        The remaining battery capacity.
        """
        return self._hub._mcall(self._me, 'capacity_left')

    def temperature(self) -> float:
        """
        Gets the temperature of the battery.

        Returns:
        The temperature in degrees Celsius.
        """
        return self._hub._mcall(self._me, 'temperature')

    def charger_detect(self) -> Union[bool, int]:
        """
        Checks what type of charger was detected.

        Returns:
        See charging constants for all possible return values. Returns False
        if it failed to detect a charger.
        """
        return self._hub._mcall(self._me, 'charger_detect')

    def info(self) -> dict:
        """
        Gets status information about the battery.

        This returns a dictionary of the form:

        {
            # Battery measurements as documented above.
            'battery_capacity_left': 100
            'temperature': 25.7,
            'charge_current': 248,
            'charge_voltage': 8294,

            # Filtered version of the battery voltage.
            'charge_voltage_filtered': 8287,

            # A list of active errors. See constants given below.
            'error_state': [0],

            # Charging state. See constants given below.
            'charger_state': 2,
        }

        Returns:
        Battery status information.
        """
        return self._hub._mcall(self._me, 'info')

    # Battery status values

    # The battery is happy.
    BATTERY_NO_ERROR = 0

    # The battery temperature is outside of the expected range.
    BATTERY_HUB_TEMPERATURE_CRITICAL_OUT_OF_RANGE = -1

    # The battery temperature is outside of the critical range.
    BATTERY_TEMPERATURE_OUT_OF_RANGE = -2

    # The battery temperature sensor is not working.
    BATTERY_TEMPERATURE_SENSOR_FAIL = -3

    # Something is wrong with the battery.
    BATTERY_BAD_BATTERY = -4

    # The battery voltage is too low.
    BATTERY_VOLTAGE_TOO_LOW = -5

    # No battery detected.
    BATTERY_MISSING = -6

    # Charger types

    # No charger detected.
    USB_CH_PORT_NONE = 0

    # Standard downstream port (typical USB port).
    USB_CH_PORT_SDP = 1

    # Charging Downstream Port (wall charger).
    USB_CH_PORT_CDP = 2

    # Dedicated charging port (high current USB port).
    USB_CH_PORT_DCP = 3

    # Charging states

    # There was a problem charging the battery.
    CHARGER_STATE_FAIL = -1

    # The battery is discharging.
    CHARGER_STATE_DISCHARGING = 0

    # The battery is charging.
    CHARGER_STATE_CHARGING_ONGOING = 1

    # The battery is fully charged.
    CHARGER_STATE_CHARGING_COMPLETED = 2


# noinspection PyProtectedMember
class Bluetooth:
    def __init__(self, hub: Hub, me: str):
        self._hub = hub
        self._me = me

    def discoverable(self, *args, **kwargs):
        """
        discoverable() -> int
        discoverable(time: int) -> None
        Gets or sets the Bluetooth classic discoverability state.

        Parameters:
        time – For how many seconds the hub should be discoverable. During this
        time, you can find the hub when you search for Bluetooth devices using your computer or phone.

        Returns:
        If no argument is given, this returns the remaining number of seconds
        that the hub is discoverable. Once the hub is no longer discoverable, it returns 0.
        """
        return self._hub._mcall(self._me, 'discoverable', *args, **kwargs)

    def info(self) -> dict:
        """
        Gets a dictionary of the form:

        {
            # The Bluetooth device MAC address.
            'mac_addr': '38:0B:3C:A2:E1:E4',

            # The Bluetooth device UUID.
            'device_uuid': '03970000-1800-3500-1551-383235373836'

            # The outgoing service UUID.
            'service_uuid': '',

            # Bluetooth name of the device.
            'name': 'LEGO Hub 38:0B:3C:A2:E1:E4',

            # iPod Accessory Protocol (iAP) status dictionary.
            'iap': {
                'device_version': 7,
                'authentication_revision': 1,
                'device_id': -1,
                'certificate_serial_no': '54D2891DEC5E5104F7132BC3059365CB',
                'protocol_major_version': 3,
                'protocol_minor_version': 0
            },

            # A list of devices that the hub has been connected to.
            'known_devices': [],
        }

        Returns:
        Bluetooth subsystem information dictionary similar to the example above,
        or None if the Bluetooth subsystem is not running.
        """
        return self._hub._mcall(self._me, 'info')

    def forget(self, address: str) -> bool:
        """
        Removes a device from the list of known Bluetooth devices.

        Parameters:
        address – Bluetooth address of the form '01:23:45:67:89:AB'.

        Returns:
        True if a valid address was given, or False if not.
        """
        return self._hub._mcall(self._me, 'forget', address)

    def lwp_advertise(self, *args, **kwargs):
        """
        lwp_advertise() -> int
        lwp_advertise(timeout: int) -> None
        Gets or sets the Bluetooth Low Energy LEGO Wireless protocol advertising state.

        Parameters:
        time – For how many seconds the hub should advertise the LEGO Wireless
        Protocol. During this time, you can find the hub when you search for
        Bluetooth devices using your computer or phone.

        Returns:
        If no argument is given, this returns the remaining number of seconds
        that the hub will advertise. Once the hub is no longer advertising, it returns 0.
        """
        return self._hub._mcall(self._me, 'lwp_advertise', *args, **kwargs)

    def lwp_bypass(self, *args, **kwargs):
        """
        lwp_bypass() -> bool
        lwp_bypass(bypass: bool) -> None
        Controls whether the LEGO Wireless Protocol is bypassed when using Bluetooth Low Energy.

        Parameters:
        bypass – Choose True to bypass the LEGO Wireless protocol or choose False to enable it.

        Returns:
        If no argument is given, this returns the current bypass state.
        """
        return self._hub._mcall(self._me, 'lwp_bypass', *args, **kwargs)


class Buttons:
    def __init__(self, hub: Hub, me: str):
        self.left = Button(hub, f'{me}.left')
        self.right = Button(hub, f'{me}.right')
        self.center = Button(hub, f'{me}.center')
        self.connect = Button(hub, f'{me}.connect')


# noinspection PyProtectedMember
class Button:
    def __init__(self, hub: Hub, me: str):
        self._hub = hub
        self._me = me

    def __repr__(self):
        return self._me

    def is_pressed(self) -> bool:
        """
        Gets the state of the button.

        Returns:
        True if it is pressed, False otherwise.
        """
        return self._hub._mcall(self._me, 'is_pressed')

    def was_pressed(self) -> bool:
        """
        Checks if this button was pressed since this method was last called.

        Returns:
        True if it was pressed at least once since the previous call, False otherwise.
        """
        return self._hub._mcall(self._me, 'was_pressed')

    def presses(self) -> int:
        """
        Gets the number of times this button was pressed since this method was last called.

        Returns:
        The number of presses since the last call.
        """
        return self._hub._mcall(self._me, 'presses')


class Image:
    def __init__(self, string_or_width: Union[str, int, list],
                 height: Optional[int] = None, buffer: Optional[bytes] = None):
        if isinstance(string_or_width, list):
            assert height is None and buffer is None
            self.pixels = string_or_width
        elif isinstance(string_or_width, str):
            assert height is None and buffer is None
            self.pixels = self._parse_string(string_or_width)
        else:
            width = string_or_width
            if height is None:
                raise ValueError("height must not be None")
            if buffer is None:
                buffer = b'\0' * (width * height)
            else:
                if len(buffer) != width * height:
                    raise ValueError("buffer length must be width*height")
            self.pixels = [[buffer[i * width + j] for j in range(width)] for i in range(height)]

    @staticmethod
    def _parse_string(s):
        if ':' in s:
            rows = s.split(':')
        else:
            rows = s.split('\n')
        pixels = [[int(c) for c in row.strip()] for row in rows if row.strip()]
        if not all(len(row) == len(pixels[0]) for row in pixels):
            raise ValueError("Not all rows have equal width")
        return pixels

    def width(self):
        return len(self.pixels[0])

    def height(self):
        return len(self.pixels)

    def shift(self, x: int, y: int):
        w = self.width()
        h = self.height()
        return Image([[(self.pixels[y0 + y][x0 + x] if (0 <= y0 + y < h and 0 <= x0 + x < w) else 0)
                       for x0 in range(w)]
                      for y0 in range(h)])

    def shift_left(self, n: int):
        return self.shift(n, 0)

    def shift_right(self, n: int):
        return self.shift(-n, 0)

    def shift_up(self, n: int):
        return self.shift(0, n)

    def shift_down(self, n: int):
        return self.shift(0, -n)

    def get_pixel(self, x: int, y: int) -> int:
        return self.pixels[y][x]

    def set_pixel(self, x: int, y: int, brightness: int):
        self.pixels[y][x] = brightness

    def __eq__(self, other):
        return self.pixels == other.pixels

    def __repr__(self):
        s = ''.join(''.join(str(x) for x in row) + ':' for row in self.pixels)
        return f'Image({s!r})'


Image.ANGRY = Image('90009:09090:00000:99999:90909:')
Image.ARROW_E = Image('00900:00090:99999:00090:00900:')
Image.ARROW_N = Image('00900:09990:90909:00900:00900:')
Image.ARROW_NE = Image('00999:00099:00909:09000:90000:')
Image.ARROW_NW = Image('99900:99000:90900:00090:00009:')
Image.ARROW_S = Image('00900:00900:90909:09990:00900:')
Image.ARROW_SE = Image('90000:09000:00909:00099:00999:')
Image.ARROW_SW = Image('00009:00090:90900:99000:99900:')
Image.ARROW_W = Image('00900:09000:99999:09000:00900:')
Image.ASLEEP = Image('00000:99099:00000:09990:00000:')
Image.BUTTERFLY = Image('99099:99999:00900:99999:99099:')
Image.CHESSBOARD = Image('09090:90909:09090:90909:09090:')
Image.CLOCK1 = Image('00090:00090:00900:00000:00000:')
Image.CLOCK2 = Image('00000:00099:00900:00000:00000:')
Image.CLOCK3 = Image('00000:00000:00999:00000:00000:')
Image.CLOCK4 = Image('00000:00000:00900:00099:00000:')
Image.CLOCK5 = Image('00000:00000:00900:00090:00090:')
Image.CLOCK6 = Image('00000:00000:00900:00900:00900:')
Image.CLOCK7 = Image('00000:00000:00900:09000:09000:')
Image.CLOCK8 = Image('00000:00000:00900:99000:00000:')
Image.CLOCK9 = Image('00000:00000:99900:00000:00000:')
Image.CLOCK10 = Image('00000:99000:00900:00000:00000:')
Image.CLOCK11 = Image('09000:09000:00900:00000:00000:')
Image.CLOCK12 = Image('00900:00900:00900:00000:00000:')
Image.CONFUSED = Image('00000:09090:00000:09090:90909:')
Image.COW = Image('90009:90009:99999:09990:00900:')
Image.DIAMOND = Image('00900:09090:90009:09090:00900:')
Image.DIAMOND_SMALL = Image('00000:00900:09090:00900:00000:')
Image.DUCK = Image('09900:99900:09999:09990:00000:')
Image.FABULOUS = Image('99999:99099:00000:09090:09990:')
Image.GHOST = Image('99999:90909:99999:99999:90909:')
Image.GIRAFFE = Image('99000:09000:09000:09990:09090:')
Image.GO_DOWN = Image('00000:99999:09990:00900:00000:')
Image.GO_LEFT = Image('00090:00990:09990:00990:00090:')
Image.GO_RIGHT = Image('09000:09900:09990:09900:09000:')
Image.GO_UP = Image('00000:00900:09990:99999:00000:')
Image.HAPPY = Image('00000:09090:00000:90009:09990:')
Image.HEART = Image('09090:99999:99999:09990:00900:')
Image.HEART_SMALL = Image('00000:09090:09990:00900:00000:')
Image.HOUSE = Image('00900:09990:99999:09990:09090:')
Image.MEH = Image('09090:00000:00090:00900:09000:')
Image.MUSIC_CROTCHET = Image('00900:00900:00900:99900:99900:')
Image.MUSIC_QUAVER = Image('00900:00990:00909:99900:99900:')
Image.MUSIC_QUAVERS = Image('09999:09009:09009:99099:99099:')
Image.NO = Image('90009:09090:00900:09090:90009:')
Image.PACMAN = Image('09999:99090:99900:99990:09999:')
Image.PITCHFORK = Image('90909:90909:99999:00900:00900:')
Image.RABBIT = Image('90900:90900:99990:99090:99990:')
Image.ROLLERSKATE = Image('00099:00099:99999:99999:09090:')
Image.SAD = Image('00000:09090:00000:09990:90009:')
Image.SILLY = Image('90009:00000:99999:00909:00999:')
Image.SKULL = Image('09990:90909:99999:09990:09990:')
Image.SMILE = Image('00000:00000:00000:90009:09990:')
Image.SNAKE = Image('99000:99099:09090:09990:00000:')
Image.SQUARE = Image('99999:90009:90009:90009:99999:')
Image.SQUARE_SMALL = Image('00000:09990:09090:09990:00000:')
Image.STICKFIGURE = Image('00900:99999:00900:09090:90009:')
Image.SURPRISED = Image('09090:00000:00900:09090:00900:')
Image.SWORD = Image('00900:00900:00900:09990:00900:')
Image.TARGET = Image('00900:09990:99099:09990:00900:')
Image.TORTOISE = Image('00000:09990:99999:09090:00000:')
Image.TRIANGLE = Image('00000:00900:09090:99999:00000:')
Image.TRIANGLE_LEFT = Image('90000:99000:90900:90090:99999:')
Image.TSHIRT = Image('99099:99999:09990:09990:09990:')
Image.UMBRELLA = Image('09990:99999:00900:90900:09900:')
Image.XMAS = Image('00900:09990:00900:09990:99999:')
Image.YES = Image('00000:00009:00090:90900:09000:')
Image.ALL_CLOCKS = (
    Image.CLOCK12, Image.CLOCK1, Image.CLOCK2, Image.CLOCK3,
    Image.CLOCK4, Image.CLOCK5, Image.CLOCK6, Image.CLOCK7,
    Image.CLOCK8, Image.CLOCK9, Image.CLOCK10, Image.CLOCK11)
Image.ALL_ARROWS = (
    Image.ARROW_N, Image.ARROW_NE, Image.ARROW_E, Image.ARROW_SE,
    Image.ARROW_S, Image.ARROW_SW, Image.ARROW_W, Image.ARROW_NW)


# noinspection PyProtectedMember
class Display:
    def __init__(self, hub: Hub, me: str):
        self._hub = hub
        self._me = me

    def clear(self):
        """
        Turns off all the pixels.
        """
        return self._hub._mcall(self._me, 'clear')

    def rotation(self, rotation: int):
        """
        Rotates the display clockwise relative to its current orientation.

        Parameters:
        rotation – How many degrees to rotate.

        Raises:
        ValueError – If the argument is not a multiple of 90.
        """
        return self._hub._mcall(self._me, rotation)

    def align(self, *args, **kwargs) -> int:
        """
        align() -> int
        align(face: int) -> int

        Rotates the display by aligning the top with the given face of the hub.

        Parameters:
        face – Choose hub.FRONT, hub.BACK, hub.LEFT, or hub.RIGHT.

        Returns:
        The new or current alignment.
        """
        return self._hub._mcall(self._me, 'align', *args, **kwargs)

    def invert(self, *args, **kwargs) -> bool:
        """
        invert() -> bool
        invert(invert: bool) -> bool

        Inverts all pixels. This affects what is currently displayed, as well as
        everything you display afterwards.

        In the inverted state, the brightness of each pixel is the opposite of
        the normal state. If a pixel has brightness b, it will be displayed with
        brightness 9 - b.

        Parameters:
        invert – Choose True to activate the inverted state. Choose False to
        restore the normal state.

        Returns:
        The new or current inversion state.
        """
        return self._hub._mcall(self._me, 'invert', *args, **kwargs)

    def pixel(self, *args, **kwargs):
        """
        pixel(x: int, y: int) -> int
        pixel(x: int, y: int, brightness: int) -> None
        Gets or sets the brightness of one pixel.

        Parameters:
        x – Pixel position counted from the left, starting at zero.
        y – Pixel position counted from the top, starting at zero.
        brightness – Brightness between 0 (fully off) and 9 (fully on).

        Returns:
        If no brightness is given, this returns the brightness of the selected
        pixel. Otherwise it returns None.
        """
        return self._hub._mcall(self._me, 'pixel', *args, **kwargs)

    def show(self, *args, **kwargs):
        """
        show(image: hub.Image) -> None
        show(image: Iterable[hub.Image], delay=400, clear=False, wait=True, loop=False, fade=0) -> None
        Shows an image or a sequence of images.

        Except for image, all arguments must be specified as keywords.

        Parameters:
        image – The image or iterable of images to be displayed.

        Keyword Arguments:
        delay – Delay between each image in the iterable.
        clear – Choose True to clear the display after showing the last image in the iterable.
        wait – Choose True to block your program until all images are shown.
            Choose False to show all images in the background while your program continues.
        loop – Choose True repeat the sequence of images for ever. Choose False to show it only once.
        fade – Sets the transitional behavior between images in the sequence:
            0: The image will appear immediately.
            1: The image will appear immediately.
            2: The image fades out while the next image fades in.
            3: Images will scroll to the right.
            4: Images will scroll to the left.
            5: Images will fade in, starting from an empty display.
            6: Images will fade out, starting from the original image.
        """
        return self._hub._mcall(self._me, 'show', *args, **kwargs)


# noinspection PyProtectedMember
class Motion:
    def __init__(self, hub: Hub, me: str):
        self._hub = hub
        self._me = me

    def accelerometer(self, filtered=False) -> (int, int, int):
        """
        Gets the acceleration of the hub along the x, y, and z axis.

        Parameters:
        filtered – Selecting True gives a more stable value, but it is delayed
        by 10-100 milliseconds. Selecting False gives the unfiltered value.

        Returns:
        Acceleration of the hub with units of cm/s^2. On a perfectly level
        surface, this gives (0, 0, 981).
        """
        return self._hub._mcall(self._me, 'accelerometer', filtered)

    def gyroscope(self, filtered=False) -> (int, int, int):
        """
        Gets the angular velocity of the hub along the x, y, and z axis.

        Parameters:
        filtered – Selecting True gives a more stable value, but it is delayed
        by 10-100 milliseconds. Selecting False gives the unfiltered value.

        Returns:
        Angular velocity with units of degrees per second.
        """
        return self._hub._mcall(self._me, 'gyroscope', filtered)

    def align_to_model(self, top: int, front: int) -> None:
        """
        Sets the default hub orientation and/or calibrates the gyroscope.

        The hub must not move while calibrating. It takes about one second by default.

        Changing the model alignment affects most other methods in this module.
        They will now be relative to the hub alignment that you specify.

        Keyword Arguments:
        top – Which hub side is at the top of your model. See the hub constants for all possible values.
        front – Which hub side is on the front of your model.
        nsamples – Number of samples for calibration between 0 and 10000. It is 100 by default.
        """
        return self._hub._mcall(self._me, 'align_to_model', top, front)

    def yaw_pitch_roll(self, *args, **kwargs):
        """
        yaw_pitch_roll() -> Tuple[int, int, int]
        yaw_pitch_roll(yaw_preset: int) -> None
        yaw_pitch_roll(yaw_correction: float) -> None
        Gets the yaw, pitch, and roll angles of the hub, or resets the yaw.

        The yaw_correction is an optional keyword argument to improve the
        accuracy of the yaw value after one full turn. To use it:
        * Reset the yaw angle to zero using hub.motion.yaw_pitch_roll(0).
        * Rotate the hub smoothly exactly one rotation clockwise.
        * Call `error = hub.motion.yaw_pitch_roll()[0]` to get the yaw error.
        * The error should be 0. If it is not, you can set the correction using
          hub.motion.yaw_pitch_roll(yaw_correction=error).
        * For even more accuracy, you can turn clockwise 5 times, and use
          `error / 5` as the correction factor.

        Keyword Arguments:
        yaw_preset – Sets the current yaw to the given value (-180 to 179).
        yaw_correction – Adjusts the gain of the yaw axis values. See the yaw adjustment section below.

        Returns:
        If no arguments are given, this returns a tuple of yaw, pitch, and roll values in degrees.
        """
        return self._hub._mcall(self._me, 'yaw_pitch_roll', *args, **kwargs)

    def orientation(self) -> int:
        """
        Gets which hub side of the hub is mostly pointing up.

        Returns:
        Number representing which side is up. See hub constants for all possible values.
        """
        return self._hub._mcall(self._me, 'orientation')

    def gesture(self) -> Optional[int]:
        """
        Gets the most recent gesture that the hub has made since this function was last called.

        Returns:
        Number representing the gesture. See motion constants for all possible
        values. If no gesture was detected since this function was last called, it returns None.
        """
        return self._hub._mcall(self._me, 'gesture')

    # The hub was tapped.
    TAPPED = 0

    # The hub was quickly tapped twice.
    DOUBLETAPPED = 1

    # The hub was shaken.
    SHAKE = 2

    # The hub fell.
    FREEFALL = 3


class Ports:
    def __init__(self, hub: Hub, me: str):
        self.A = Port(hub, f'{me}.A')
        self.B = Port(hub, f'{me}.B')
        self.C = Port(hub, f'{me}.C')
        self.D = Port(hub, f'{me}.D')
        self.E = Port(hub, f'{me}.E')
        self.F = Port(hub, f'{me}.F')

    # A device was detached from the port.
    DETACHED = 0

    # A new device is attached to the port.
    ATTACHED = 1

    # The port is Powered Up compatible.
    MODE_DEFAULT = 0

    # The port operates as a raw full duplex logic level serial port.
    MODE_FULL_DUPLEX = 1

    # The port operates as a raw half duplex differential level serial port.
    MODE_HALF_DUPLEX = 2

    # The port operates as general input and output Pin.
    MODE_GPIO = 3


# noinspection PyProtectedMember
class Sound:
    def __init__(self, hub: Hub, me: str):
        self._hub = hub
        self._me = me

    def volume(self, *args, **kwargs):
        """
        volume(volume: int) -> None
        volume() -> int
        Sets the volume of the speaker.

        Parameters:
        Volume – Volume between 0 (no sound) and 10 (maximum volume).

        Returns:
        If no argument is given, this returns the current volume.
        """
        return self._hub._mcall(self._me, 'volume', *args, **kwargs)

    def beep(self, freq=1000, time=1000, waveform=0) -> None:
        """
        Starts beeping with a given frequency, duration, and wave form.

        Keyword Arguments:
        freq – Frequency of the beep in Hz (100 - 10000).
        time – Duration of the beep in milliseconds (0 - 32767).
        waveform – Wave form used for the beep. See constants for all possible values.
        """
        return self._hub._mcall(self._me, 'beep', freq, time, waveform)

    def play(self, filename: str, rate=16000) -> None:
        """
        Starts playing a sound file.

        The sound file must be raw 16 bit data at 16 kHz.

        Parameters:
        filename – Absolute path to the sound file.

        Keyword Arguments:
        rate – Playback speed in Hz.
        """
        return self._hub._mcall(self._me, 'play', filename, rate)

    # The beep is a smooth sine wave.
    SOUND_SIN = 0

    # The beep is a loud and raw square wave.
    SOUND_SQUARE = 1

    # The beep has a triangular wave form.
    SOUND_TRIANGLE = 2

    # The beep has a sawtooth-shaped wave form.
    SOUND_SAWTOOTH = 3


# noinspection PyProtectedMember
class Supervision:
    def __init__(self, hub: Hub, me: str):
        self._hub = hub
        self._me = me

    def info(self) -> dict:
        """
        Gets status information from the subsystem that supervises the hub.

        This returns a dictionary of the form:

        {
            # Checks if the peak current is too high.
            'peek_current_too_high': False,

            # Checks if the current is too high.
            'continous_current_too_high': False,

            # The current value in mA.
            'continuous_current': 60,

            # Checks if the hub temperature is too high.
            'temperature_too_high': False
        }

        Returns:
        Supervision status information.
        """
        return self._hub._mcall(self._me, 'info')


# noinspection PyProtectedMember
class Port:
    def __init__(self, hub: Hub, me: str):
        self._hub = hub
        self._me = me

        self.device = Device(hub, f'{me}.device')
        self.motor = Motor(hub, f'{me}.motor')
        # Not implemented yet
        self.p5 = Pin(hub, f'{me}.p5')
        self.p6 = Pin(hub, f'{me}.p6')

    def __repr__(self):
        return self._me

    def pwm(self, value: int) -> None:
        """
        Applies a PWM signal to the power pins of the port or device.

        A PWM value of 0 has the same effect as float().

        Parameters:
        value – PWM value between -100 and +100. The polarity of the PWM signal
        matches the sign of the value. A value of 0 stops the PWM signal and
        leaves the port driver in the floating state.
        """
        return self._hub._mcall(self._me, 'pwm', value)

    def mode(self, *args, **kwargs) -> None:
        """
        mode(mode: int, baud_rate=2400) -> None
        Sets the mode of the port.

        This command initiates the mode change, but it does not wait for completion.

        Parameters
        mode – Mode value. See the port constants for all possible values
        baud_rate – New baud rate of the port, if applicable.
        """
        return self._hub._mcall(self._me, 'mode', *args, **kwargs)

    def info(self):
        """
        Gets information about the port and devices attached to it.

        If no Powered Up device is plugged in or the port is not in the default mode, this returns {'type': None}.

        If a Powered Up device is detected, it returns a dictionary of the form:

        {
            # The device type. For example, the Medium Angular Motor.
            'type': 75,

            # List of modes that can be combined. Each number encodes
            # bitflags of device modes that may be combined. In this
            # example, you may combine modes 1, 2, or 3 (14 == 1110),
            # or combine modes 0, 1, 2, and 3 (15 = 1111).

            # Device baud rate for UART devices.
            'speed': 115200,

            # A list of dictionaries with information about each mode.
            'modes': [mode0_info, mode1_info, ...],

            # A 24-byte unique serial number.
            'uid': bytearray(b'\x00G\x00%\rG909523\x00\x00 ... '),

            # Device hardware version.
            'hw_version': 4

            # Device firmware version.
            'fw_version': 268435456,
        }

        The modes entry above is a list of dictionaries, one for each mode.
        For example, reading info()['modes'][3] on the Medium Angular Motor gives:

        {
            # Name of the mode.
            'name': 'APOS',

            # Symbol or unit of the mode.
            'symbol': 'DEG',

            # Data format for this mode.
            'format': {
                # Number of values returned by this mode.
                'datasets': 1,

                # Data type (int8=0, int16=1, int32=2, float=3).
                'type': 1,

                # Number of digits.
                'figures': 3,

                # Number of digits after the decimal point.
                'decimals': 0
            },
            # 48 bit flags that indicate what this device can do or needs.
            'capability': b'\x22\x00\x00\x00\x01\x04',

            #  The output mapping bits as an 8 bit value.
            'map_out': 8,

            #  The input mapping bits as an 8 bit value.
            'map_in': 8,

            # The minimum and maximum range of the data as a percentage.
            'pct': (-200.0, 200.0),

            # The minimum and maximum range of the value in the SI unit.
            'si': (-180.0, 179.0),

            # The minimum and maximum range of raw data.
            'raw': (-180.0, 179.0)
        }
        Returns:
        Information dictionary as documented above.
        """
        return self._hub._mcall(self._me, 'info')

    # Methods for use with MODE_FULL_DUPLEX and MODE_HALF_DUPLEX

    def baud(self, baud: int) -> None:
        """
        Sets the baud rate of the serial port.

        Parameters:
        baud – The new baud rate.
        """
        return self._hub._mcall(self._me, 'baud', baud)

    def read(self, n: int) -> bytes:
        """
        Reads from the serial port.

        Parameters:
        n – the requested amount of bytes.

        Returns:
        the bytes that were read
        """
        return self._hub._mcall(self._me, 'read', n)

    def write(self, write: bytes) -> int:
        """
        Writes bytes to the serial port.

        Parameters:
        write – The string to write.

        Returns:
        The number of bytes written.
        """
        return self._hub._mcall(self._me, 'write', write)


# noinspection PyProtectedMember
class Device:
    def __init__(self, hub: Hub, me: str):
        self._hub = hub
        self._me = me

    def __repr__(self):
        return self._me

    def get(self, *args, **kwargs) -> list:
        """
        get(format: Optional[int]) -> list
        Gets the values that the active device mode provides.

        Parameters
        format – Format of the data. Choose FORMAT_RAW, FORMAT_PCT, or FORMAT_SI.

        Returns
        Values or measurements representing the device state.
        """
        return self._hub._mcall(self._me, 'get', *args, **kwargs)

    def mode(self, *args, **kwargs):
        """
        mode(mode: int) → None
        mode(mode: int, data: bytes) -> None
        mode(mode: Iterable[Tuple[int, int]]) -> None
        mode() -> Iterable[Tuple[int, int]]
        Configures the device mode or multi-mode.

        Most Powered Up devices can work in different modes. Each mode makes it
        do or measure different things. After selecting one mode or a list of
        modes, the corresponding measured values are accessible via the get method.

        Each mode can provide one or more values. For each mode in a multi-mode
        list, you must select which value of that mode you want. For example,
        to read value 0 of mode 0 as well as values 2 and 3 of mode 5, the mode
        argument is: [(0, 0), (5, 2), (5, 3)]. See Port.info to learn which modes can be combined.

        Incorrect arguments or incompatible mode settings will be ignored without errors.

        Parameters:
        mode – A single mode integer or a list of multi-mode tuples.
        data – Data to write to the selected mode. When using this argument, modes must be a single integer.

        Returns:
        When setting the mode, it returns None. If you don’t give any arguments, this returns the currently active mode.
        """
        return self._hub._mcall(self._me, 'mode', *args, **kwargs)

    def pwm(self, value: int) -> None:
        """
        Applies a PWM signal to the power pins of the port or device.

        A PWM value of 0 has the same effect as float().

        Parameters:
        value – PWM value between -100 and +100. The polarity of the PWM signal
        matches the sign of the value. A value of 0 stops the PWM signal and
        leaves the port driver in the floating state.
        """
        return self._hub._mcall(self._me, 'pwm', value)

    def write_direct(self, data: bytes) -> None:
        """
        Sends a message to the device using the wired Powered Up protocol.

        The data must be formatted using the Powered Up specification, which may
        include a command or message type and a payload. The required checksum
        will be added automatically.

        Parameters
        data – The Powered Up data message. Must not exceed 9 bytes.
        """
        return self._hub._mcall(self._me, 'write_direct', data)

    # The data has no particular unit.
    FORMAT_RAW = 0

    # The data is a percentage.
    FORMAT_PCT = 1

    # The data has SI units, if available.
    FORMAT_SI = 2


# noinspection PyProtectedMember
class Motor:
    def __init__(self, hub: Hub, me: str):
        self._hub = hub
        self._me = me

    def __repr__(self):
        return self._me

    def get(self, *args, **kwargs) -> list:
        """
        get(format: Optional[int]) -> list
        Gets the values that the active device mode provides.

        Parameters
        format – Format of the data. Choose FORMAT_RAW, FORMAT_PCT, or FORMAT_SI.

        Returns
        Values or measurements representing the device state.
        """
        return self._hub._mcall(self._me, 'get', *args, **kwargs)

    def mode(self, *args, **kwargs):
        """
        mode(mode: Iterable[Tuple[int, int]]) -> None
        Configures which measurements get() must return.

        Motors with rotation sensors have four useful modes:
            0: PWM currently applied to the motor.
            1: Speed as a percentage of design speed.
            2: Angular position in degrees relative to the position on boot.
            3: Absolute position in degrees between -180 and +179.

        The default mode setting used by the MINDSTORMS app is
        [(1, 0), (2, 0), (3, 0), (0, 0)]. When you select this mode, you can read all values as follows:

            speed_pct, rel_pos, abs_pos, pwm = hub.port.A.motor.get()

        Simple motors like train motors only have mode 0.
        See Device.mode for details and other use cases of modes.

        Parameters:
        mode – A list of multi-mode tuples.
        """
        return self._hub._mcall(self._me, 'mode', *args, **kwargs)

    def pwm(self, value: int) -> None:
        """
        Applies a PWM signal to the power pins of the port or device.

        A PWM value of 0 has the same effect as float().

        Parameters:
        value – PWM value between -100 and +100. The polarity of the PWM signal
        matches the sign of the value. A value of 0 stops the PWM signal and
        leaves the port driver in the floating state.
        """
        return self._hub._mcall(self._me, 'pwm', value)

    def float(self) -> None:
        """
        Floats (coasts) the motor, as if disconnected from the hub.
        """
        return self._hub._mcall(self._me, 'float')

    def brake(self) -> None:
        """
        Passively brakes the motor, as if shorting the motor terminals.
        """
        return self._hub._mcall(self._me, 'brake')

    def hold(self) -> None:
        """
        Actively hold the motor in its current position.
        """
        return self._hub._mcall(self._me, 'hold')

    def busy(self, typ=0) -> bool:
        """
        Checks whether the motor is busy changing modes, or executing a motor command such as running to a position.

        Parameters:
        type – Choose BUSY_MODE or BUSY_MOTOR.

        Returns:
        Whether the motor is busy with the specified activity.
        """
        return self._hub._mcall(self._me, 'busy', typ)

    def run_at_speed(self, *args, **kwargs) -> None:
        """
        run_at_speed(speed: int) -> None
        run_at_speed(speed: int, max_power: int, acceleration: int, deceleration: int, stall: bool) -> None
        Starts running a motor at the given speed.

        If a keyword argument is not given, its default value will be used.

        Parameters:
        speed – Sets the speed as a percentage of the rated speed for this motor.
            Positive means clockwise, negative means counterclockwise.

        Keyword Arguments:
        max_power – Sets percentage of maximum power used during this command.
        acceleration – The time in milliseconds (0-10000) for the motor to reach maximum rated speed from standstill.
        deceleration – The time in milliseconds (0-10000) for the motor to stop
            when starting from the maximum rated speed.
        stall – Selects whether the motor should stop when stalled (True) or not (False).
        """
        return self._hub._mcall(self._me, 'run_at_speed', *args, **kwargs)

    def run_for_time(self, *args, **kwargs) -> None:
        """
        run_for_time(msec: int) → None
        run_for_time(msec: int, speed: int, max_power: int, stop: int,
                     acceleration: int, deceleration: int, stall: bool) -> None
        Runs a motor for a given amount of time.

        If a keyword argument is not given, its default value will be used.

        Parameters:
        msec – How long the motor should run in milliseconds. Negative values will be treated as zero.

        Keyword Arguments:
        speed – Sets the speed as a percentage of the rated speed for this motor.
            Positive means clockwise, negative means counterclockwise.
        max_power – Sets percentage of maximum power used during this command.
        stop – How to stop. Choose type: Choose STOP_FLOAT, STOP_BRAKE, or STOP_HOLD.
        acceleration – The time in milliseconds (0-10000) for the motor to reach maximum rated speed from standstill.
        deceleration – The time in milliseconds (0-10000) for the motor to stop
            when starting from the maximum rated speed.
        stall – Selects whether the motor should stop trying to reach the endpoint when stalled (True) or not (False).
        """
        return self._hub._mcall(self._me, 'run_for_time', *args, **kwargs)

    def run_for_degrees(self, *args, **kwargs) -> None:
        """
        run_for_degrees(degrees: int) -> None
        run_for_degrees(degrees: int, speed: int, max_power: int, stop: int,
                        acceleration: int, deceleration: int, stall: bool) -> None
        Runs a motor for a given number of degrees at a given speed.

        If a keyword argument is not given, its default value will be used.

        Parameters:
        degrees – How many degrees to rotate relative to the starting point.

        Keyword Arguments:
        speed – Sets the speed as a percentage of the rated speed for this motor.
            If degrees > 0 and speed > 0, the motor turns clockwise.
            If degrees > 0 and speed < 0, the motor turns counterclockwise.
            If degrees < 0 and speed > 0, the motor turns clockwise.
            If degrees < 0 and speed < 0, the motor turns counterclockwise.
        max_power – Sets percentage of maximum power used during this command.
        stop – How to stop. Choose type: Choose STOP_FLOAT, STOP_BRAKE, or STOP_HOLD.
        acceleration – The time in milliseconds (0-10000) for the motor to reach maximum rated speed from standstill.
        deceleration – The time in milliseconds (0-10000) for the motor to stop
            when starting from the maximum rated speed.
        stall – Selects whether the motor should stop trying to reach the endpoint when stalled (True) or not (False).
        """
        return self._hub._mcall(self._me, 'run_for_degrees', *args, **kwargs)

    def run_to_position(self, *args, **kwargs) -> None:
        """
        run_to_position(position: int) -> None
        run_to_position(position: int, speed: int, max_power: int, stop: int,
                        acceleration: int, deceleration: int, stall: bool) -> None
        Runs a motor to the given position.

        The angular position is measured relative to the motor position when the
        hub was turned on or when the motor was plugged in. You can preset this
        starting position using preset.

        If a keyword argument is not given, its default value will be used.

        Parameters:
        position – Position to rotate to.

        Keyword Arguments:
        speed – Sets the speed as a percentage of the rated speed for this motor. The sign of the speed will be ignored.
        max_power – Sets percentage of maximum power used during this command.
        stop – How to stop. Choose type: Choose STOP_FLOAT, STOP_BRAKE, or STOP_HOLD.
        acceleration – The time in milliseconds (0-10000) for the motor to reach maximum rated speed from standstill.
        deceleration – The time in milliseconds (0-10000) for the motor to stop
            when starting from the maximum rated speed.
        stall – Selects whether the motor should stop trying to reach the endpoint when stalled (True) or not (False).
        """
        return self._hub._mcall(self._me, 'run_to_position', *args, **kwargs)

    def preset(self, position: int) -> None:
        """
        Presets the starting position used by run_to_position.

        Parameters:
        position – The new position preset.
        """
        return self._hub._mcall(self._me, 'preset', position)

    def pid(self, *args, **kwargs):
        """
        pid() -> tuple
        pid(p: int, i: int, d: int) -> None
        Sets the p, i, and d constants of the motor PID controller.

        Parameters:
        p – Proportional constant.
        i – Integral constant.
        d – Derivative constant.

        Returns:
        If no arguments are given, this returns the values previously set by the user, if any.
        The system defaults cannot be read.
        """
        return self._hub._mcall(self._me, 'pid', *args, **kwargs)

    def default(self, *args, **kwargs):
        """
        default() -> dict
        default(speed: int, max_power: int, acceleration: int, deceleration: int,
                stop: int, pid: tuple, stall: bool) -> None
        Gets or sets the motor default settings. These are used by some of the
        methods listed above, when no explicit argument is given.

        Keyword Arguments:
        speed – The default speed.
        max_power – The default max_power.
        acceleration – The default acceleration.
        deceleration – The default deceleration.
        stop – The default stop argument.
        pid – Tuple of p, i, and d. See also pid.
        stall – The default stall argument.

        Returns:
        If no arguments are given, this returns the current settings.
        """
        return self._hub._mcall(self._me, 'default', *args, **kwargs)

    def pair(self, other_motor: Motor) -> Union[MotorPair, bool, None]:
        """
        Pairs this motor to other_motor to create a MotorPair object.

        You can only pair two different motors that are not already part of another pair.
        Both motors must be of the same type.

        Parameters:
        other_motor – The motor to pair to.

        Returns:
        On success, this returns the MotorPair object. It returns False to
        indicate an incompatible pair or None for other errors.
        """
        my_letter = self._me.split('.')[2]
        other_letter = other_motor._me.split('.')[2]
        pair_name = f'pair{my_letter}{other_letter}'
        b = self._hub._pb.exec_(f'{pair_name} = {self._me}.pair({other_motor._me}); print({pair_name})')
        if b == b'False':
            return False
        elif b == b'None':
            return None
        if not b.startswith(b'MotorPair('):
            raise RuntimeError(f"Unexpected MotorPair reply: {b!r}")
        return MotorPair(self._hub, pair_name, self, other_motor)

    # The port is busy configuring the device mode.
    BUSY_MODE = 0

    # The motor is busy executing a command.
    BUSY_MOTOR = 1

    # When stopping, the motor floats. See also float().
    STOP_FLOAT = 0

    # When stopping, the motor brakes. See also brake().
    STOP_BRAKE = 1

    # When stopping, the motor holds position. See also hold().
    STOP_HOLD = 2

    # The motor command completed successfully.
    EVENT_COMPLETED = 0

    # The motor command was interrupted.
    EVENT_INTERRUPTED = 1

    # The motor command stopped because the motor was stalled.
    EVENT_STALLED = 2


# noinspection PyProtectedMember
class MotorPair:
    def __init__(self, hub: Hub, me: str, primary: Motor, secondary: Motor):
        self._hub = hub
        self._me = me
        self._primary = primary
        self._secondary = secondary

    def __repr__(self):
        return self._me

    def id(self) -> int:
        """
        Gets the motor pair identifier.

        Returns:
        The motor pair identifier.
        """
        return self._hub._mcall(self._me, 'id')

    def primary(self) -> Motor:
        """
        Gets the motor object on which pair was called to create this pair object.

        Returns:
        The primary motor.
        """
        return self._primary

    def secondary(self) -> Motor:
        """
        Gets the motor object that was the parameter in the pair call to create this pair object.

        Returns:
        The secondary motor.
        """
        return self._secondary

    def unpair(self) -> bool:
        """
        Uncouples the two motors so they can be used by other pairs.

        Returns:
        True if the operation succeeded, False otherwise.
        """
        return self._hub._mcall(self._me, 'unpair')

    def float(self) -> None:
        """
        Floats (coasts) both motors, as if disconnected from the hub.
        """
        return self._hub._mcall(self._me, 'float')

    def brake(self) -> None:
        """
        Passively brakes both motors, as if shorting the motor terminals.
        """
        return self._hub._mcall(self._me, 'brake')

    def hold(self) -> None:
        """
        Actively holds both motor in their current position.
        """
        return self._hub._mcall(self._me, 'hold')

    def pwm(self, pwm_0: int, pwm_1: int) -> None:
        """
        Applies PWM signals to the power pins of both motors.

        A PWM value of 0 has the same effect as float().

        Parameters:
        pwm_0 – PWM value between -100 and +100 for the primary motor.
            The polarity of the PWM signal matches the sign of the value.
            A value of 0 stops the PWM signal and leaves the port driver in the floating state.
        pwm_1 – PWM value for the secondary motor, as above.
        """
        return self._hub._mcall(self._me, 'pwm', pwm_0, pwm_1)

    def run_at_speed(self, *args, **kwargs) -> None:
        """
        run_at_speed(speed_0: int, speed_1: int) -> None
        run_at_speed(speed_0: int, speed_1: int, max_power: int, acceleration: int, deceleration: int) -> None
        Starts running both motor at given speeds.

        If a keyword argument is not given, its default value will be used.

        Parameters:
        speed_0 – Sets the speed of the primary motor as a percentage of the
            rated speed for this motor. Positive means clockwise, negative means counterclockwise.
        speed_1 – Sets the speed of the secondary motor, as above.

        Keyword Arguments:
        max_power – Sets percentage of maximum power used during this command.
        acceleration – The time in milliseconds (0-10000) for a motor to reach maximum rated speed from standstill.
        deceleration – The time in milliseconds (0-10000) for a motor to stop
            when starting from the maximum rated speed.
        """
        return self._hub._mcall(self._me, 'run_at_speed', *args, **kwargs)

    def run_for_time(self, *args, **kwargs) -> None:
        """
        run_for_time(msec: int) -> None
        run_for_time(msec: int, speed_0: int, speed_1: int, max_power: int,
                     acceleration: int, deceleration: int, stop: int) -> None
        Runs both motors for a given amount of time.

        If a keyword argument is not given, its default value will be used.

        Parameters:
        msec – How long the motors should run in milliseconds. Negative values will be treated as zero.

        Keyword Arguments:
        speed_0 – Sets the speed of the primary motor as a percentage of the
            rated speed for this motor. Positive means clockwise, negative means counterclockwise.
        speed_1 – Sets the speed of the secondary motor, as above.
        max_power – Sets percentage of maximum power used during this command.
        acceleration – The time in milliseconds (0-10000) for a motor to reach maximum rated speed from standstill.
        deceleration – The time in milliseconds (0-10000) for a motor to stop
            when starting from the maximum rated speed.
        stop – How to stop. Choose type: Choose STOP_FLOAT, STOP_BRAKE, or STOP_HOLD.
        """
        return self._hub._mcall(self._me, 'run_for_time', *args, **kwargs)

    def run_for_degrees(self, *args, **kwargs) -> None:
        """
        run_for_degrees(degrees: int) -> None
        run_for_degrees(degrees: int, speed_0: int, speed_1: int, max_power: int,
                        acceleration: int, deceleration: int, stop: int) -> None
        Runs the motors for the given number of degrees, on average.

        If a keyword argument is not given, its default value will be used.

        Parameters:
        degrees – How many degrees to rotate relative to the starting point, on
            average. The ratio of the speeds will determine how many degrees
            each motor rotates. The sign of degrees is ignored. The directions
            are determined by the speed arguments, if given.

        Keyword Arguments:
        speed_0 – Sets the speed of the primary motor as a percentage of the
            rated speed for this motor. Positive means clockwise, negative means counterclockwise.
        speed_1 – Sets the speed of the secondary motor, as above.
        max_power – Sets percentage of maximum power used during this command.
        max_power – Sets percentage of maximum power used during this command.
        acceleration – The time in milliseconds (0-10000) for a motor to reach maximum rated speed from standstill.
        deceleration – The time in milliseconds (0-10000) for a motor to stop
            when starting from the maximum rated speed.
        stop – How to stop. Choose type: Choose STOP_FLOAT, STOP_BRAKE, or STOP_HOLD.
        """
        return self._hub._mcall(self._me, 'run_for_degrees', *args, **kwargs)

    def run_to_position(self, *args, **kwargs) -> None:
        """
        run_to_position(position_0: int, position_1: int) -> None
        run_to_position(position_0: int, position_1: int, speed: int, max_power: int,
                        acceleration: int, deceleration: int, stop: int) -> None
        Runs both motors to a given angular position.

        If a keyword argument is not given, its default value will be used.

        Parameters:
        position_0 – Angular position target for the primary motor.
        position_1 – Angular position target for the secondary motor.

        Keyword Arguments:
        speed – Sets the speed of the motor that has to travel the farthest, as
            a percentage of the rated speed for this motor. The other motor
            speed will be selected such that both motors arrive at their respective positions at the same time.
        max_power – Sets percentage of maximum power used during this command.
        max_power – Sets percentage of maximum power used during this command.
        acceleration – The time in milliseconds (0-10000) for a motor to reach maximum rated speed from standstill.
        deceleration – The time in milliseconds (0-10000) for a motor to stop
            when starting from the maximum rated speed.
        stop – How to stop. Choose type: Choose STOP_FLOAT, STOP_BRAKE, or STOP_HOLD.
        """
        return self._hub._mcall(self._me, 'run_to_position', *args, **kwargs)

    def preset(self, position_0: int, position_1: int) -> None:
        """
        Presets the starting positions used by run_to_position.

        Parameters:
        position_0 – The new position preset of the primary motor.
        position_1 – The new position preset of the secondary motor.
        """
        return self._hub._mcall(self._me, 'preset', position_0, position_1)

    def pid(self, p: int, i: int, d: int) -> None:
        """
        Sets the p, i, and d constants of the MotorPair PID controllers.

        Parameters:
        p – Proportional constant.
        i – Integral constant.
        d – Derivative constant.
        """
        return self._hub._mcall(self._me, 'pid', p, i, d)


# noinspection PyProtectedMember
class Pin:
    def __init__(self, hub: Hub, me: str):
        self._hub = hub
        self._me = me

    def __repr__(self):
        return self._me

    def direction(self, *args, **kwargs) -> int:
        """
        direction(direction: Optional[int]) -> int
        Gets and sets the direction of the pin.

        Parameters:
        direction – Choose 0 to make the pin an input or 1 to make it an output.

        Returns:
        The configured direction.
        """
        return self._hub._mcall(self._me, 'direction', *args, **kwargs)

    def value(self, *args, **kwargs) -> int:
        """
        value(value: Optional[int]) -> int
        Gets and sets the logic value of the pin.

        Parameters:
        value – Choose 1 to make the pin high or 0 to make it low.
            If the pin is configured as an input, this argument is ignored.

        Returns:
        Logic value of the pin.
        """
        return self._hub._mcall(self._me, 'value', *args, **kwargs)


# noinspection PyProtectedMember
class Os:
    def __init__(self, hub):
        self._hub = hub

        self.sep = '/'
        methods = [
            'remove', 'chdir', 'dupterm', 'getcwd', 'ilistdir', 'listdir',
            'mkdir', 'mount', 'rename', 'rmdir', 'stat', 'statvfs', 'sync',
            'umount', 'uname', 'unlink']
        for method in methods:
            setattr(self, method, partial(self._call, method))

    def _call(self, method, *args, **kwargs):
        return self._hub._mcall('os', method, *args, **kwargs)
