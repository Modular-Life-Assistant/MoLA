from core import NotificationManager
from helpers.modules.BaseModule import BaseModule


class NotificationModule(BaseModule):
    def internal_init(self):
        super().internal_init()
        NotificationManager.register(self.name, self.send)

    def send(self, msg, image=None, sound=None):
        """ Send message."""
        raise NotImplementedError()
