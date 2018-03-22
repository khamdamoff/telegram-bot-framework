from bot.action.standard.info.formatter import ApiObjectInfoFormatter
from bot.action.util.format import ChatFormatter
from bot.api.api import Api
from bot.api.domain import ApiObject


CHAT_TYPE_PRIVATE = "private"


class ChatInfoFormatter(ApiObjectInfoFormatter):
    def __init__(self, api: Api, chat: ApiObject, bot_user: ApiObject, user: ApiObject):
        super().__init__(api, chat)
        self.bot_user = bot_user
        self.user = user

    def format(self, full_info: bool = False):
        """
        :param full_info: If True, adds more info about the chat. Please, note that this additional info requires
            to make THREE synchronous api calls.
        """
        chat = self.api_object
        if full_info:
            self.__format_full(chat)
        else:
            self.__format_simple(chat)

    def __format_full(self, chat: ApiObject):
        chat = self.api.getChat(chat_id=chat.id)
        description = self._text(chat.description)
        invite_link = self._invite_link(chat.invite_link)
        pinned_message = self._pinned_message(chat.pinned_message)
        sticker_set_name = self._group_sticker_set(chat.sticker_set_name)
        member_count = self.api.getChatMembersCount(chat_id=chat.id)
        admins = self._get_admins(chat)
        admin_count = len(admins)
        me_admin = self._yes_no(self._is_admin(self.bot_user, admins))
        you_admin = self._yes_no(self._is_admin(self.user, admins))
        self.__format_simple(chat)
        self._add_info("Description", description)
        self._add_info("Invite link", invite_link)
        self._add_info("Pinned message", pinned_message)
        self._add_info("Group sticker set", sticker_set_name)
        self._add_info("Members", member_count)
        self._add_info("Admins", admin_count, "(not counting other bots)")
        self._add_info("Am I admin", me_admin)
        self._add_info("Are you admin", you_admin)

    def _get_admins(self, chat: ApiObject):
        if chat.type == CHAT_TYPE_PRIVATE:
            return ()
        return list(self.api.getChatAdministrators(chat_id=chat.id))

    def __format_simple(self, chat: ApiObject):
        full_data = ChatFormatter(chat).full_data
        title = self._text(chat.title)
        username = self._username(chat.username)
        _type = chat.type
        _id = chat.id
        all_members_are_admins = self._yes_no(chat.all_members_are_administrators)
        self._add_title(full_data)
        self._add_empty()
        self._add_info("Title", title)
        self._add_info("Username", username)
        self._add_info("Type", _type)
        self._add_info("Id", _id)
        self._add_info("All members are admins", all_members_are_admins)
