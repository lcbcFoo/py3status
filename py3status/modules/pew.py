# -*- coding: utf-8 -*-
"""
Display Pew! notifications on the bar.

Configuration parameters:
    format: display format for this module (default "[Pew! {summary}][\|{body}]")
    timeout: notification timeout for this module (default 10)

Format placeholders:
    {summary} notification summary, eg "You received 1 new message"
    {body} notification body, eg "Cops just left. You can come in now."

@author lasers

Examples:
```
# change format, colors, urgent
pew {
    format = '\?if=summary&color=orangered Pew! '
    format += '[\?color=orange {summary}]'
    format += '[\?color=darkgray \|[\?color=yellow {body}]]'
    allow_urgent = False
}

# show bell
pew {
    format = '[\?if=summary Pew! ]'
}
```

SAMPLE OUTPUT
{'full_text': 'Pew!', 'urgent': True}
"""

from dbus import SessionBus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from threading import Thread
from time import sleep

PARAM_STRING = "eavesdrop=true, member='Notify', "
PARAM_STRING += "interface='org.freedesktop.Notifications'"


class Py3status:
    """
    """

    # available configuration parameters
    format = "[Pew! {summary}][\|{body}]"
    timeout = 10

    def post_config_hook(self):
        self._hide_notification()
        t = Thread(target=self._start_loop)
        t.daemon = True
        t.start()

    def _start_loop(self):
        DBusGMainLoop(set_as_default=True)
        bus = SessionBus()
        bus.add_match_string_non_blocking(PARAM_STRING)
        bus.add_message_filter(self._show_notification)
        self.mainloop = GLib.MainLoop()
        self.mainloop.run()

    def _hide_notification(self):
        self.body, self.summary, self.urgent = None, None, False

    def _show_notification(self, bus, notification):
        notification = [format(arg) for arg in notification.get_args_list()]
        self.body = " ".join(notification[4].split("\n"))
        self.summary = " ".join(notification[3].split("\n"))
        self.urgent = True
        self.py3.update()

        sleep(self.timeout)
        self._hide_notification()
        self.py3.update()

    def pew(self):
        return {
            "urgent": self.urgent,
            "cached_until": self.py3.CACHE_FOREVER,
            "full_text": self.py3.safe_format(
                self.format, {"body": self.body, "summary": self.summary}
            ),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
