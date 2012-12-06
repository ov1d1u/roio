import sys, os, gtk

from pygtkhelpers.delegates import WindowView
from pygtkhelpers.utils import gsignal
from pygtkhelpers.gthreads import AsyncTask
from pygtkhelpers.debug.dialogs import install_hook

from network import ROIONetwork
from views import FirstContent, LogIn, Content

if '--debug' in sys.argv:
    install_hook()

fh = open('ui/gtk-2.0/gtkrc')
rc_string = fh.read()
fh.close()
gtk.rc_parse_string(rc_string)

class RoioGUI(WindowView):
    builder_file = "roio.glade"

    def __init__(self, *args, **kwargs):
    	super(RoioGUI, self).__init__()
        gtk.rc_reset_styles(gtk.settings_get_for_screen(self.mainWindow.get_screen()))

    	# initial values
    	self.is_maximized = bool(self.mainWindow.get_state() == gtk.gdk.WINDOW_STATE_MAXIMIZED)
        self.account_data = {}

    	# customize the UI
    	pixbuf = gtk.gdk.pixbuf_new_from_file('ui/top_bar.png')
    	(pixmap, mask) = pixbuf.render_pixmap_and_mask(255)
    	style = self.topbox.get_style().copy()
    	style.bg_pixmap[gtk.STATE_NORMAL] = pixmap
    	self.topbox.set_style(style)

    	self.windowBox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
    	self.bodyBox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#222222"))
    	self.bottomBox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#191919"))

        # init network handler
        self.net = ROIONetwork()

        # we're ready to go
        self.show_first_content()

    # child calls
    def show_first_content(self):
        self._clear_content()
        self.statusLabel.set_text('Connecting...')
        AsyncTask(self.net.send_hello, self.ping_status).start()
        self.body_content = self.add_slave(FirstContent(self), 'mainContent')

    def show_login(self):
        self._clear_content()
        self.log_in = self.add_slave(LogIn(self), 'mainContent')

    def show_content(self, account_data):
        self._clear_content()
        self.account_data = account_data
        self.content = self.add_slave(Content(self), 'mainContent')

    # events
    def on_topbox__button_press_event(self, object, event):
    	self.mainWindow.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)

    def on_close__button_press_event(self, object, event):
    	return True
    def on_close__button_release_event(self, object, event):
    	self.on_mainWindow__delete_event(None, event)
    def on_close__enter_notify_event(self, object, event):
        self.image_close.set_from_file('ui/close_small_prelight.png')
    def on_close__leave_notify_event(self, object, event):
        self.image_close.set_from_file('ui/close_small.png')

    def on_maximise__button_release_event(self, object, event):
    	if self.is_maximized:
    		self.mainWindow.unmaximize()
    	else:
    		self.mainWindow.maximize()
    def on_maximise__button_press_event(self, object, event):
    	return True
    def on_maximise__enter_notify_event(self, object, event):
        self.image_max.set_from_file('ui/restore_prelight.png')
    def on_maximise__leave_notify_event(self, object, event):
        self.image_max.set_from_file('ui/restore.png')

    def on_minimise__button_press_event(self, object, event):
    	return True
    def on_minimise__button_release_event(self, object, event):
    	self.mainWindow.iconify()
    def on_minimise__enter_notify_event(self, object, event):
        self.image_min.set_from_file('ui/minimize_prelight.png')
    def on_minimise__leave_notify_event(self, object, event):
        self.image_min.set_from_file('ui/minimize.png')

    def on_mainWindow__window_state_event(self, window, event):
    	self.is_maximized = bool(event.new_window_state == gtk.gdk.WINDOW_STATE_MAXIMIZED)

    def on_bodyBox__button_press_event(self, object, event):
    	return True

    def on_resizer__button_press_event(self, object, event):
    	self.mainWindow.begin_resize_drag(gtk.gdk.WINDOW_EDGE_SOUTH_EAST, event.button, int(event.x_root), int(event.y_root), event.time)

    def on_mainWindow__delete_event(self, window, event):
    	os._exit(0)

    # other methods
    def ping_status(self, data):
        if data.status == 'ok':
            self.body_content.signin_btn.set_sensitive(True)
            self.statusLabel.set_text('Connection OK, ping: {0}ms'.format(data.duration))
        else:
            self.body_content.signin_btn.set_sensitive(False)
            self.statusLabel.set_text("COULDN'T CONNECT TO SERVER!")

    # 'private' methods
    def _clear_content(self):
        del self.slaves[:]
        for child in self.mainContent.children():
            child.destroy()

def start_roio():
    fs = RoioGUI()
    fs.show_and_run()

if __name__ == '__main__':
    start_roio()