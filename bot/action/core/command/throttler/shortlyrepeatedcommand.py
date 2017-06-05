from bot.action import chatsettings
from bot.action.chatsettings import ChatSettings
from bot.action.core.command.throttler import Throttler
from bot.action.util.textformat import FormattedText


class ShortlyRepeatedCommandThrottler(Throttler):
    def __init__(self, api):
        self.api = api
        self.recent_commands = {}

    def should_execute(self, event):
        current_date = event.message.date
        self.__cleanup_recent_commands(current_date)
        command_key = CommandKey(event)
        if command_key not in self.recent_commands:
            throttling_state = CommandThrottlingState(event)
            if not throttling_state.has_expired(current_date):
                # it has not expired immediately, throttling is enabled
                self.recent_commands[command_key] = throttling_state
        else:
            throttling_state = self.recent_commands[command_key]
            throttling_state.add_invocation()
        if throttling_state.should_warn():
            self.__send_throttling_warning(event, throttling_state)
        return throttling_state.should_execute()

    def __cleanup_recent_commands(self, current_date):
        for key, state in self.recent_commands.copy().items():
            if state.has_expired(current_date):
                del self.recent_commands[key]

    def __send_throttling_warning(self, event, throttling_state):
        remaining_seconds = throttling_state.remaining_seconds(event.message.date)
        message = FormattedText().bold("Ignoring repeated command.").normal(" Try again in ")\
            .code_inline(remaining_seconds).normal(" seconds.")\
            .build_message()
        message.to_chat_replying(event.message)
        self.api.send_message(message)


class CommandKey:
    def __init__(self, event):
        chat_id = event.chat.id
        command = event.command
        command_args = event.command_args
        reply_to_message_id = event.message.reply_to_message.message_id if event.message.reply_to_message else None
        self.__key = (chat_id, command, command_args, reply_to_message_id)

    def __hash__(self):
        return hash(self.__key)

    def __eq__(self, other):
        return self.__key == other.__key


class CommandThrottlingState:
    def __init__(self, event):
        self.chat_settings = chatsettings.repository.get_for_event(event)
        self.first_invocation = event.message.date
        self.number_of_invocations = 1

    def add_invocation(self):
        self.number_of_invocations += 1

    def should_execute(self):
        return self.number_of_invocations <= 1

    def should_warn(self):
        return self.number_of_invocations == 2

    def has_expired(self, current_date):
        throttling_seconds = self.chat_settings.get(ChatSettings.THROTTLING_SECONDS)
        expiration_date = current_date - throttling_seconds
        return self.first_invocation <= expiration_date

    def remaining_seconds(self, current_date):
        throttling_seconds = self.chat_settings.get(ChatSettings.THROTTLING_SECONDS)
        expiration_date = current_date - throttling_seconds
        return self.first_invocation - expiration_date
