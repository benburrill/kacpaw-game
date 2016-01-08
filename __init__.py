import json
import shelve
import jinja2
from operator import attrgetter
from collections import defaultdict

import kacpaw

class Player:
    def __init__(self, user, comment):
        self.user = user
        self.comment = comment

class GameShelf(shelve.DbfilenameShelf):
    WORD_JOIN = "join"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # map of users to comments
        self.setdefault("players", {})
        # list of ignored comments
        self.setdefault("ignored", [])
        # map users to their crime
        self.setdefault("banned", defaultdict(list))

    def wants_to_join(self, comment):
        return WORD_JOIN in comment.text_content

    def comment_is_new(self, comment):
        return comment not in self["players"].values() and comment not in self["ignored"]

    def user_is_playing(self, user):
        return user in self["players"]

    def user_is_banned(self, user):
        return user in self["banned"]

    def ignore_comment(self, comment):
        if comment not in self["ignored"]:
            self["ignored"].append(comment)

    def ban_player(self, player, reason): # todo: maybe take a comment parameter so we can tell the player that they messed up before we ban them 
        if self.user_is_playing(player):
            self["ignored"].append(self["players"].pop(player))
        self["banned"][player].append(reason)

    def get_new_players(self, program, session):
        for comment in program.get_replies():
            author = comment.get_author()

            # todo: when we implement the ability to switch comment threads, old comments will be added
            # to ignored.  We need to do something special here to notice that the user has switched and
            # change their comment to the new comment

            # todo: move some of this stuff out of this function
            if self.user_is_playing(author):
                comment.reply(self.session, "You are already playing!  Go to {.url} to continue playing".format(
                    self["players"][author]))
                self.ignore_comment(comment)

            elif self.user_is_banned(author):
                comment.reply(session, "You are not allowed to play!\nReason(s): {}".format(
                    "\n".join(self["banned"][author])))
                self.ignore_comment(comment)

            elif self.comment_is_new(comment) and self.wants_to_join(comment):
                comment.reply(session, "Welcome to the game, {.name}".format(author))
                self["players"][author] = comment


class Game:
    def __init__(self, session, program, loader, save_file, template_file):
        self.session = session
        self.program = program
        self.template_file = template_file
        self.shelf = GameShelf(save_file, writeback=True)
        self.env = jinja2.Environment(loader=loader, undefined=jinja2.StrictUndefined)

    def update_program(self, world):
        code = self.env.get_template(self.template_file).render(
            world_json=json.dumps(dict(self.shelf, **world)),
            title=self.program.get_metadata()["title"]
        )
        self.program.edit(self.session, code=code)

    def update_player(self, player):
        for player in self.shelf["players"]:
            pass

    def __del__(self):
        self.shelf.close()

if __name__ == "__main__":
    import os
    session = kacpaw.KASession(os.environ["KA_USERNAME"], os.environ["KA_PASSWORD"])
    print("Logged into", session.user.name + "'s", "account")
    program = kacpaw.Program("5495235907551232")
    print("On the program", program.title)

    Game(session, program, jinja2.PackageLoader(__name__), "game1.shelf", "program.html").update_program({"x": 42})