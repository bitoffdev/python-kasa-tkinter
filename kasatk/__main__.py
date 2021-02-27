#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys
import threading
import tkinter
import tkinter.font
import tkinter.ttk

from typing_extensions import TypedDict

import kasa

logger = logging.getLogger(__name__)


class LightState(TypedDict):
    on_off: int
    mode: str
    hue: int
    saturation: int
    color_temp: int
    brightness: int


async def update_bulb(bulb, brightness=None, hue=None, saturation=None):
    if brightness != None:
        await bulb.set_brightness(brightness)
    if hue != None or saturation != None:
        state: LightState = await bulb.get_light_state()
        await bulb.set_hsv(
            hue if hue != None else state["hue"],
            saturation if saturation != None else state["saturation"],
            brightness if brightness != None else state["brightness"],
        )


class ScrollableFrame(tkinter.ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tkinter.Canvas(self)
        self.scrollable_frame = tkinter.ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas_frame_id = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        self.scrollbar = tkinter.ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill=tkinter.BOTH, expand=True)
        self.scrollbar.pack(side="right", fill=tkinter.Y)

        # update the inner content frame when the canvas resizes
        self.canvas.bind("<Configure>", self._resize_canvas_frame)

        # bind mouse scroll only when the mouse is over our element
        self.canvas.bind("<Enter>", self._bind_mouse)
        self.canvas.bind("<Leave>", self._unbind_mouse)

    def _resize_canvas_frame(self, event):
        """Resize the width of the inner content frame"""
        # Note that we intentionally do NOT update the height of the inner
        # frame. We want that to be based on the amount of content so that we
        # can scroll it.
        self.canvas.itemconfig(self.canvas_frame_id, width=event.width)

    def _bind_mouse(self, event):
        if sys.platform == "linux":
            self.canvas.bind_all("<Button-4>", self._on_mouse_scroll)
            self.canvas.bind_all("<Button-5>", self._on_mouse_scroll)
        else:
            self.canvas.bind_all("<MouseWheel>", self._on_mouse_scroll)

    def _unbind_mouse(self, event):
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mouse_scroll(self, event):
        logger.info("ScrollableFrame._on_mousewheel()")

        # Button 5 is "scroll up" in Linux. It seems that event.delta may just
        # be zero on Linux.
        if sys.platform == "linux" and event.num == 5:
            self.canvas.yview_scroll(1, "units")
        # Button 4 is "scroll down" in Linux. It seems that event.delta may
        # just be zero on Linux.
        elif sys.platform == "linux" and event.num == 4:
            self.canvas.yview_scroll(-1, "units")

        if sys.platform != "linux" and event.delta != 0:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class EditableText(tkinter.Frame):
    def __init__(self, container, initial_text_value, callback):
        super(self.__class__, self).__init__(container)

        self.callback = callback

        self.text = tkinter.StringVar(value=initial_text_value)
        self.child_widgets = []
        self._render_static_mode()

    def _edit_mode_start(self, event=None):
        for widget in self.child_widgets:
            widget.destroy()
        self._render_edit_mode()

    def _edit_mode_finish(self, event=None):
        self.callback(self.text.get())
        for widget in self.child_widgets:
            widget.destroy()
        self._render_static_mode()

    def _render_static_mode(self):
        """render non-editable text"""
        label_font = tkinter.font.Font(
            family="Helvetica", name="appHighlightFont", size=12, weight="bold"
        )

        text_label = tkinter.Label(self, text=self.text.get(), font=label_font)
        text_label.pack(side=tkinter.LEFT)

        edit_label = tkinter.Label(self, image=self.pencil_icon)
        edit_label.bind("<ButtonRelease-1>", self._edit_mode_start)
        edit_label.pack(side=tkinter.LEFT)

        self.child_widgets.append(text_label)
        self.child_widgets.append(edit_label)

    def _render_edit_mode(self):
        text_entry = tkinter.Entry(self, textvariable=self.text)
        text_entry.pack(side=tkinter.LEFT)
        text_entry.bind("<Return>", self._edit_mode_finish)

        self.child_widgets.append(text_entry)

    @property
    def pencil_icon(self):
        """... note:: Make sure to store a reference to the result, as the
        BitmapImage may otherwise get garbage collected. Passing it to
        tkinter.Label is not sufficient.
        (https://stackoverflow.com/a/31959529/2796349)
        """
        if not hasattr(self, "_pencil_icon"):
            self._pencil_icon = tkinter.BitmapImage(
                data=b"#define image_width 16\n#define image_height 16\nstatic char image_bits[] = {\n0x00,0x1c,0x00,0x3e,0x00,0x7f,0x80,0xf7,0xc0,0xf3,0xe0,0x79,0xf0,0x3c,0x78,\n0x1e,0x3c,0x0f,0x9c,0x07,0xcc,0x03,0xfc,0x01,0xfc,0x00,0x7c,0x00,0xff,0xff,\n0xff,0xff\n};"
            )
        return self._pencil_icon


class BulbFrame(tkinter.Frame):
    async def _hue_callback(self):
        return await update_bulb(self.bulb, None, self.hue_slider.get())

    async def _saturation_callback(self):
        return await update_bulb(self.bulb, saturation=self.saturation_slider.get())

    async def _brightness_callback(self):
        return await update_bulb(self.bulb, self.brightness_slider.get())

    async def _power_callback(self):
        self.power_button["state"] = tkinter.DISABLED

        try:
            await (self.bulb.turn_off() if self.bulb.is_on else self.bulb.turn_on())
            await self.bulb.update()
        finally:
            self.power_button["relief"] = "sunken" if self.bulb.is_on else "raised"
            self.power_button["text"] = "Turn Off" if self.bulb.is_on else "Turn On"
            self.power_button["state"] = tkinter.NORMAL

    @classmethod
    def for_bulb(cls, loop, bulb: kasa.SmartBulb, config, *args, **kwargs):
        """Create a new bulb frame given a SmartBulb

        ... note:: I think using a classmethod here is a better approach than
        breaking the initializer interface of the parent Frame class.
        """
        self = cls(*args, **kwargs)
        self.bulb = bulb

        self.hue_label = tkinter.Label(self, text="hue")
        self.saturation_label = tkinter.Label(self, text="saturation")
        self.brightness_label = tkinter.Label(self, text="brightness")

        self.hue_slider = tkinter.Scale(
            self, from_=0, to=360, orient=tkinter.HORIZONTAL
        )
        self.hue_slider.bind(
            "<ButtonRelease-1>",
            lambda event, self=self, loop=loop: asyncio.run_coroutine_threadsafe(
                self._hue_callback(), loop
            ),
        )
        self.hue_slider.set(self.bulb.hsv[0])

        self.saturation_slider = tkinter.Scale(
            self, from_=0, to=100, orient=tkinter.HORIZONTAL
        )
        self.saturation_slider.bind(
            "<ButtonRelease-1>",
            lambda event, self=self, loop=loop: asyncio.run_coroutine_threadsafe(
                self._saturation_callback(), loop
            ),
        )
        self.saturation_slider.set(self.bulb.hsv[1])

        self.brightness_slider = tkinter.Scale(
            self, from_=0, to=100, orient=tkinter.HORIZONTAL
        )
        self.brightness_slider.bind(
            "<ButtonRelease-1>",
            lambda event, self=self, loop=loop: asyncio.run_coroutine_threadsafe(
                self._brightness_callback(), loop
            ),
        )
        self.brightness_slider.set(self.bulb.brightness)

        bulb_name = getattr(self.bulb, "alias", None) or self.bulb.mac

        # TODO See if we can update the device alias instead of just logging it
        # here
        EditableText(
            self, bulb_name, lambda new_device_name: logger.info(new_device_name)
        ).grid(column=0, row=0, columnspan=4)

        self.power_button = tkinter.Button(
            self,
            text="Turn Off" if self.bulb.is_on else "Turn On",
            width=12,
            relief="sunken" if self.bulb.is_on else "raised",
        )
        self.power_button.bind(
            "<ButtonRelease-1>",
            lambda event, self=self, loop=loop: asyncio.run_coroutine_threadsafe(
                self._power_callback(), loop
            ),
        )

        self.power_button.grid(column=0, row=2, sticky="ns")
        # self.power_button.grid(column=0, row=2)

        self.hue_label.grid(column=1, row=1)
        self.hue_slider.grid(column=1, row=2)

        self.saturation_label.grid(column=2, row=1)
        self.saturation_slider.grid(column=2, row=2, sticky="ns")

        self.brightness_label.grid(column=3, row=1)
        self.brightness_slider.grid(column=3, row=2, sticky="ns")

        return self


class KasaDevices(tkinter.Frame):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        # create an asyncio event loop running in a secondary thread
        def exception_handler(loop, context):
            loop.call_soon_threadsafe(
                logger.error, "Caught exception {}".format(context)
            )

        self.event_loop = asyncio.new_event_loop()
        self.event_loop.set_exception_handler(exception_handler)
        self.event_thread = threading.Thread(target=self.event_loop.run_forever)
        self.event_thread.start()

        self.device_lock = asyncio.Lock()
        # list of kasa devices
        self.kasa_devices = []
        # mapping from mac address to widget
        self.device_widgets = {}

        async def process_devices():
            # queue to process discovered devices
            #
            # this must be called from within the loop:
            #   https://stackoverflow.com/a/53724990/2796349
            self.device_queue = asyncio.Queue()

            while True:
                new_item = await self.device_queue.get()
                logging.info("Discovered device: {}".format(repr(new_item)))
                try:
                    await self.add_device(new_item)
                except Exception as exc:
                    logging.error(exc)

        self.event_loop.create_task(process_devices())

        # TODO make sure that self.device_queue exists before exiting this function

        self.refresh_button = tkinter.Button(
            self, text="Refresh", command=self.start_refresh
        )
        self.refresh_button.pack(fill=tkinter.X)

    @property
    def _bulbs(self):
        return list(
            filter(lambda d: d.device_type == kasa.DeviceType.Bulb, self.kasa_devices)
        )

    async def update_widgets(self):
        for bulb in self._bulbs:
            if bulb.mac not in self.device_widgets:
                w = BulbFrame.for_bulb(self.event_loop, bulb, self.config, master=self)
                w.pack()
                self.device_widgets[bulb.mac] = w

    async def add_device(self, device):
        await device.update()
        logger.info("add_device(device={})".format(repr(device)))
        async with self.device_lock:
            mac_addrs = [d.mac for d in self.kasa_devices]
            device_exists = mac_addrs.count(device.mac) > 0
            if device_exists:
                return
            self.kasa_devices.append(device)
        await self.update_widgets()

    async def _do_refresh(self):
        logger.info("KasaDevices._do_refresh() called")
        self.refresh_button["state"] = tkinter.DISABLED
        self.refresh_button["text"] = "Refreshing..."
        await self.clear_devices()
        await kasa.Discover.discover(on_discovered=self.device_queue.put)
        self.refresh_button["state"] = tkinter.NORMAL
        self.refresh_button["text"] = "Refresh"

    async def clear_devices(self):
        async with self.device_lock:
            for mac, widget in self.device_widgets.items():
                widget.destroy()
            self.device_widgets.clear()
            self.kasa_devices.clear()

    def start_refresh(self):
        """Returns a *concurrent* future, rather than an *asyncio* future. You
        can block on the result from a *synchronous* thread using
        self.start_refresh().result().

        :rtype: concurrent.futures.Future
        """
        logger.info("KasaDevices.start_refresh() called")

        async def call_later(coro, *args, **kwargs):
            # call later isn't particularly necessary, but by using it, out
            # exceptions will go to the asyncio exceptions handler
            self.event_loop.create_task(coro(*args, **kwargs))

        return asyncio.run_coroutine_threadsafe(
            call_later(self._do_refresh), self.event_loop
        )


def main():
    root = tkinter.Tk()
    root.title("Kasa Devices")
    root.geometry("500x400")
    root.iconbitmap("extra/icon.ico")
    scroll_frame = ScrollableFrame(root)
    KasaDevices(scroll_frame.scrollable_frame).pack()
    scroll_frame.pack(fill=tkinter.BOTH, expand=True)
    root.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        dest="verbosity",
        default=0,
        help="show verbose logging (repeat flag for increased verbosity)",
    )
    args = parser.parse_args()
    log_level = logging.CRITICAL - args.verbosity * 10
    formatter = logging.Formatter(
        "[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s",
        "%m-%d %H:%M:%S",
    )
    logging.basicConfig(level=log_level)
    root = logging.getLogger()
    hdlr = root.handlers[0]
    hdlr.setFormatter(formatter)
    main()
