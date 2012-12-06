import re, gtk, gobject
import hashlib

from pygtkhelpers.delegates import SlaveView
from pygtkhelpers.gthreads import AsyncTask

from network import ROIONetwork
net = ROIONetwork()

class FirstContent(SlaveView):
    builder_file = "firstcontent.glade"

    def __init__(self, parent):
        super(FirstContent, self).__init__()
        self.parent = parent

    # events

    def on_signin_btn__clicked(self, object):
        self.parent.show_login()


class LogIn(SlaveView):
    builder_file = "login.glade"

    def __init__(self, parent):
        super(LogIn, self).__init__()
        self._hide_register()
        self.parent = parent

        # init network handler

    def _reset_form(self):
        self.recovery_box.hide()
        self.username.set_text('')
        self.password.set_text('')
        self.password2.set_text('')
        self.real_name.set_text('')
        self.email.set_text('')
        self.error_lbl.set_label('')
        self.login_status.set_label('')

    def _hide_register(self):
        self.intro_text.show()
        self.default_buttons.show()
        self.register_box.hide()
        self.register_text.hide()

    def _validate_form(self):
        errors = {}
        if len(self.username.get_text()) < 6:
            errors[self.username] = 'Username is too short'
        elif len(self.password.get_text()) < 6:
            errors[self.password] = 'Password is too short'
        elif self.password.get_text() != self.password2.get_text():
            errors[self.password] = errors[self.password2] = "Passwords doesn't match"
        elif re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", self.email.get_text()) == None:
            errors[self.email] = 'Invalid email address'
        return errors

    def _flash_error(self, widget, step=1):
        bgcolor = None
        if step % 2:
            bgcolor = gtk.gdk.color_parse("red")

        widget.modify_base(gtk.STATE_NORMAL, bgcolor)
        step += 1
        if step < 7:
            gobject.timeout_add(500, self._flash_error, widget, step)
        return False

    def _disable_forms(self):
        self.vbox2.set_sensitive(False)

    def _enable_forms(self):
        self.vbox2.set_sensitive(True)

    def on_register_btn__clicked(self, object):
        self._reset_form()
        self.intro_text.hide()
        self.default_buttons.hide()
        self.register_box.show()
        self.register_text.show()

    def on_cancel_btn__clicked(self, object):
        self.parent.show_login()

    def on_create_btn__clicked(self, object):
        self.error_lbl.set_label('')
        username = self.username.get_text()
        password1 = self.password.get_text()
        password2 = self.password2.get_text()
        realname = self.real_name.get_text()
        email = self.email.get_text()

        errors = self._validate_form()
        if len(errors):
            for x in errors:
                self.error_lbl.set_label(errors[x])
                self._flash_error(x)
        else:
            # do the registration
            self.parent.statusLabel.set_text('Sending data...')
            data = {
                'username': username,
                'password': hashlib.md5(password1).hexdigest(),
                'realname': realname,
                'email': email
            }
            self._disable_forms()
            AsyncTask(net.new_user, self.register_response).start(data)

    def on_signin_btn__clicked(self, object):
        self.parent.statusLabel.set_text('Signing in...')
        data = {
            'username': self.username.get_text(),
            'password': hashlib.md5(self.password.get_text()).hexdigest()
        }
        self._disable_forms()
        AsyncTask(net.sign_in, self.sign_in_response).start(data)

    def on_username__changed(self, object, event=None):
        self.login_status.set_label('')

    def on_password__changed(self, object, event=None):
        self.login_status.set_label('')

    def on_forgot_lbl__activate_link(self, object, event=None):
        self.recovery_email.set_text('')
        self.recovery_status_lbl.set_text('')
        self.register_box.hide()
        self.recovery_box.show()
        return True

    def on_recovery_btn__clicked(self, object):
        self.parent.statusLabel.set_text('Please wait...')
        self._disable_forms()
        data = {
            'email': self.recovery_email.get_text()
        }
        self._disable_forms()
        AsyncTask(net.recover, self.recovery_response).start(data)

    def on_cancel_recovery_btn__clicked(self, object):
        self._reset_form()

    # network responses
    def register_response(self, data):
        self._enable_forms()
        if data.status == 'ok':
            self._reset_form()
            self._hide_register()
            self.login_status.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#00FF0C"))
            self.login_status.set_label('Your account was successfully created.\n' + \
                'You may now log on with your credentials.')
        else:
            self.error_lbl.set_label(data.data.get('message'))
        self.parent.statusLabel.set_text('')

    def sign_in_response(self, data):
        self._enable_forms()
        if data.status == 'ok':
            self.parent.statusLabel.set_text('Welcome, {0}!'.format(data.data.get('realname', '')))
            self.parent.show_content(data.data)
        else:
            self.login_status.set_label(data.data.get('message'))
            self.login_status.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("red"))
            self.parent.statusLabel.set_text('')

    def recovery_response(self, data):
        self._enable_forms()
        if data.status == 'ok':
            self.recovery_status_lbl.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#00FF0C"))
            self.recovery_status_lbl.set_text('An email with recovery details was sent.')
        else:
            self.recovery_status_lbl.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("red"))
            self.recovery_status_lbl.set_text('No account associated with this email.')
        self.parent.statusLabel.set_text('')


class Content(SlaveView):
    builder_file = "content.glade"

    def __init__(self, parent):
        super(Content, self).__init__()
        self.parent = parent

        self.favorites_btn.set_name('favorites')
        self.settings_btn.set_name('settings')
        self.toggles = [self.favorites_btn, self.settings_btn]

        self.greeting_lbl.set_text('Hi, {0}'.format(self.parent.account_data.get('realname', '')))
        self.server_message_lbl.set_text(self.parent.account_data.get('message', 'No new messages.'))

        # requesting categories
        AsyncTask(net.categories, self.categories_response).start()

    def categories_response(self, data):
        for id in data.data:
            button = self.create_category(data.data[id])
            button.show()
            self.sections_box.pack_start(button, False, False)
            self.toggles.append(button)

    def select_category(self, object, event=None):
        print event
        for button in self.toggles:
            if not button.get_name() == object.get_name():
                button.set_active(False)
            else:
                button.set_active(True)
        return True

    # network responses
    def create_category(self, data):
        from base64 import b64decode
        button = gtk.ToggleButton(use_underline=False)
        button.set_can_focus(False)
        hbox = gtk.HBox()

        # load the image
        loader = gtk.gdk.PixbufLoader()
        loader.write(b64decode(data.get('icon', '')))
        pixbuf = loader.get_pixbuf()
        loader.close()
        image = gtk.image_new_from_pixbuf(pixbuf)
        image.set_visible(True)
        
        # set the text
        label = gtk.Label(data.get('name', ''))
        label.set_visible(True)

        hbox.pack_start(image, False, False)
        hbox.pack_start(label, False, False, 5)
        hbox.show()
        button.set_name(label.get_label().lower())
        button.connect("button-press-event", self.select_category)
        button.add(hbox)
        return button
