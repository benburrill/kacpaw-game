import json
import shelve
import jinja2
from time import sleep
from collections import defaultdict
from operator import attrgetter, methodcaller

import kacpaw



# I really need to rethink basically everything here, but it works

# todo: handle comment threads that are deleted.  Currently, this will raise an error @ user = self.comment.get_author() in Player.updata
# this is a bad place for this to happen because players objects have no control over anything and can't just remove themselves
# another problem is that we need to differentiate between 500 server errors (comment removed) and connection problems
# so please don't delete your comments!

class Player:
    player_speed = 0.05
    def __init__(self, comment):
        self.comment = comment
        self.x = 0.5
        self.y = 0.5

    def get_dict(self): # get the data needed to form user json
        return {
            "x": self.x,
            "y": self.y,
            "name": self.comment.get_author().name
        }

    def parse_comment(self, comment):
        #print(comment.get_author().name, "inputed", comment.text_content)
        try:
            action, input_text = comment.text_content.lower().strip().split(maxsplit=1)
        except ValueError:
            pass
        else:
            if action == "move":
                self.x += {"l": -1, "r": 1}.get(input_text, 0) * self.player_speed
                self.y += {"u": -1, "d": 1}.get(input_text, 0) * self.player_speed

    def update(self):
        user = self.comment.get_author()
        try:
            self.parse_comment(list(filter(
                lambda reply: reply.get_author() == user,
                self.comment.get_replies()
            )).pop())
        except IndexError:
            pass


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
        return self.WORD_JOIN in comment.text_content

    def comment_is_new(self, comment):
        return (comment not in map(attrgetter("comment"), self["players"].values()) and 
            comment not in self["ignored"])

    def user_is_playing(self, user):
        return user in self["players"]

    def user_is_banned(self, user):
        return user in self["banned"]

    def ignore_comment(self, comment):
        if comment not in self["ignored"]:
            self["ignored"].append(comment)

    def ban_player(self, player, reason): # todo: maybe take a comment parameter so we can tell the player that they messed up before we ban them 
        if self.user_is_playing(player):
            self["ignored"].append(self["players"].pop(player).comment)
        self["banned"][player].append(reason)

    def get_new_players(self, program, session):
        for comment in program.get_replies():
            author = comment.get_author()

            # todo: when we implement the ability to switch comment threads, old comments will be added
            # to ignored.  We need to do something special here to notice that the user has switched and
            # change their comment to the new comment

            # todo: move some of this stuff out of this function
            if not self.comment_is_new(comment):
                continue

            elif self.user_is_playing(author):
                comment.reply(session, "You are already playing!  Go to {.url} to continue playing".format(
                    self["players"][author]))
                self.ignore_comment(comment)

            elif self.user_is_banned(author):
                comment.reply(session, "You are not allowed to play!\nReason(s): {}".format(
                    "\n".join(self["banned"][author])))
                self.ignore_comment(comment)

            elif self.wants_to_join(comment):
                comment.reply(session, "Welcome to the game, {.name}".format(author))
                self["players"][author] = Player(comment)


class Game:
    def __init__(self, session, program, loader, save_file, template_file):
        self.session = session
        self.program = program
        self.template_file = template_file
        self.shelf = GameShelf(save_file, writeback=True)
        self.env = jinja2.Environment(loader=loader, undefined=jinja2.StrictUndefined)

    def update_program(self, world):
        code = self.env.get_template(self.template_file).render(
            world_json=json.dumps(world),
            title=self.program.get_metadata()["title"]
        )
        self.program.edit(self.session, code=code)

    def run_once(self):
        self.shelf.get_new_players(self.program, self.session)
        for user, player in self.shelf["players"].items():
            player.update()

        self.update_program({
            "players": list(map(methodcaller("get_dict"), self.shelf["players"].values()))
        })

    def run_forever(self):
        while True:
            self.run_once()
            sleep(60) # wait a minute before continuing

    def __del__(self):
        self.shelf.close()


if __name__ == "__main__":
    import os
    session = kacpaw.KASession(os.environ["KA_USERNAME"], os.environ["KA_PASSWORD"])
    print("Logged into", session.user.name + "'s", "account")
    program = kacpaw.Program("5495235907551232")
    print("On the program", program.title)

    Game(session, program, jinja2.PackageLoader(__name__), "game1.shelf", "program.html").run_forever()