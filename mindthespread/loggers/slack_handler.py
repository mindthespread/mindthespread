# import logging
# from slack_bolt.adapter.socket_mode import SocketModeHandler
# from slack_bolt import App
#
#
# class SlackLogHandler(logging.Handler):
#     def __init__(self, bot_token, app_token, info_channel='logs', warning_channel='notif'):
#         super().__init__()
#         self.app = App(token=bot_token)
#         SocketModeHandler(self.app, app_token).connect()
#         self.info_channel = info_channel
#         self.warning_channel = warning_channel
#
#     def emit(self, record):
#         self.app.client.chat_postMessage(channel=self.info_channel, text=record.message)
#         if record.levelname == 'WARNING':
#             self.app.client.chat_postMessage(channel=self.warning_channel, text=record.message)
