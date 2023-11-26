from typing import Callable, Tuple, Optional

from gi.repository import GLib, Gtk, Pango

from lutris.gui.dialogs import ErrorDialog


class ProgressBox(Gtk.Box):
    """Simple, small progress bar used to monitor the update of runtime or runner components.
    This class needs only a function that returns the current progress, as a tuple of progress (0->1)
    and markup to display in a label. You can also supply a cstop function to be called when the
    stop button is clicked, or omit this to not have one."""

    StopFunction = Callable[[], None]
    ProgressFunction = Callable[[], Tuple[float, str, Optional[StopFunction]]]

    def __init__(self,
                 progress_function: ProgressFunction,
                 stop_function: StopFunction = None,
                 **kwargs):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, no_show_all=True, spacing=6, **kwargs)

        self.progress_function = progress_function
        self.stop_function = stop_function

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, visible=True, spacing=6,
                       valign=Gtk.Align.CENTER)

        self.label = Gtk.Label("", visible=False,
                               wrap=True, ellipsize=Pango.EllipsizeMode.MIDDLE,
                               xalign=0)
        vbox.pack_start(self.label, False, False, 0)

        self.progressbar = Gtk.ProgressBar(visible=True)
        self.progressbar.set_valign(Gtk.Align.CENTER)
        vbox.pack_start(self.progressbar, False, False, 0)

        self.pack_start(vbox, True, True, 0)

        self.stop_button = Gtk.Button.new_from_icon_name("media-playback-stop-symbolic", Gtk.IconSize.BUTTON)
        self.stop_button.set_visible(bool(stop_function))
        self.stop_button.get_style_context().add_class("circular")
        self.stop_button.connect("clicked", self.on_stop_clicked)
        self.pack_start(self.stop_button, False, False, 0)

        self.timer_id = GLib.timeout_add(500, self.on_update_progress)
        self.connect("destroy", self.on_destroy)

    def on_stop_clicked(self, _widget) -> None:
        if self.stop_function:
            self.stop_function()

    def on_destroy(self, _widget) -> None:
        if self.timer_id:
            GLib.source_remove(self.timer_id)

    def on_update_progress(self) -> bool:
        try:
            progress, progress_text, stop_function = self.progress_function()
            self.stop_function = stop_function
        except Exception as ex:
            ErrorDialog(ex, parent=self.get_toplevel())
            self.timer_id = None
            self.destroy()
            return False

        self.progressbar.set_fraction(min(progress, 1))
        self._set_label(progress_text or "")
        self.stop_button.set_visible(bool(stop_function))
        return True

    def _set_label(self, markup: str) -> None:
        if markup:
            if markup != self.label.get_text():
                self.label.set_markup(markup)
            self.label.show()
        else:
            self.label.hide()
