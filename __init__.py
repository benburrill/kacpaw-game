import sys
import json
import shelve
import jinja2
from time import sleep
from functools import partial
from collections import defaultdict
from operator import attrgetter, methodcaller

import kacpaw



def safe_str(val, encoding=sys.stdout.encoding, errors="xmlcharrefreplace"):
    """ 
    Handles encoding problems when converting val to a str in the encoding ``encoding``
    By default, characters that cannot be expressed with the encoding are replaced with 
    xml character escapes, but anything from docs.python.org/3/library/codecs.html#error-handlers
    will work.
    """
    return str(val)\
        .encode(encoding, errors=errors)\
        .decode(encoding, errors="ignore")

def safe_print(*args, **kwargs):
    """
    A print function that uses safe_str before printing.
    arguments:
        *args: same as print
        **kwargs: any optional kwargs from either print or safe_str
    """
    # split kwargs into two dictionaries, one with the keys ["encoding", "errors"]
    # to be passed into safe_str, and one with everything else, to be passed into print
    enc_kwds = {
        key: kwargs.pop(key) for key in dict(kwargs) 
            if key in ["encoding", "errors"]}

    print(*map(partial(safe_str, **enc_kwds), args), **kwargs)



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
            "radius": getattr(self, "radius", 25),
            "color": getattr(self, "color", 0xff006400),
            "x": self.x,
            "y": self.y,
            "name": self.comment.get_author().name
        }

    def action_move(self, input_text):
        safe_print("moving", input_text)
        self.x += {"l": -1, "r": 1}.get(input_text, 0) * self.player_speed
        self.y += {"u": -1, "d": 1}.get(input_text, 0) * self.player_speed

        self.x = max(min(self.x, 1), 0)
        self.y = max(min(self.x, 1), 0)

    def action_color(self, input_text):
        safe_print("setting color to", input_text)
        try:
            self.color = int(input_text, 0)
        except ValueError:
            pass

    def action_radius(self, input_text):
        safe_print("setting radius to", input_text)
        try:
            radius = int(input_text, 0)
        except ValueError:
            pass
        else:
            if 10 < radius < 30:
                self.radius = radius

    action_map = { # this is probably not the smartest idea, but it should work
        "move": action_move,
        "color": action_color,
        "radius": action_radius
    }

    def parse_comment(self, comment):
        safe_print(comment.get_author().name, "inputed", comment.text_content)
        try:
            action, input_text = comment.text_content.lower().strip().split(maxsplit=1)
        except ValueError:
            pass
        else:
            try: self.action_map[action](self, input_text)
            except KeyError: pass


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
            if self.comment_is_new(comment) and self.wants_to_join(comment):
                if self.user_is_playing(author):
                    safe_print(author.name, "tried to join, but is already playing")
                    comment.reply(session, "You are already playing!  Go to {.url} to continue playing".format(
                        self["players"][author].comment))
                    self.ignore_comment(comment)

                elif self.user_is_banned(author):
                    safe_print(author.name, "tried to join, but is banned")
                    comment.reply(session, "You are not allowed to play!\nReason(s): {}".format(
                        "\n".join(self["banned"][author])))
                    self.ignore_comment(comment)

                else:
                    safe_print(author.name, "has joined!")
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