import sublime
from sublime_plugin import WindowCommand, TextCommand

from ..git_command import GitCommand
from ...common import util

LOG_GRAPH_TITLE = "GRAPH"


class GsLogGraphCommand(WindowCommand, GitCommand):

    """
    Open a new window displaying an ASCII-graphic representation
    of the repo's branch relationships.
    """

    def run(self):
        repo_path = self.repo_path
        view = self.window.new_file()
        view.settings().set("git_savvy.log_graph_view", True)
        view.settings().set("git_savvy.repo_path", repo_path)
        view.settings().set("word_wrap", False)
        view.set_syntax_file("Packages/GitSavvy/syntax/graph.tmLanguage")
        view.set_name(LOG_GRAPH_TITLE)
        view.set_scratch(True)
        view.set_read_only(True)
        view.run_command("gs_log_graph_initialize")


class GsLogGraphInitializeCommand(TextCommand, GitCommand):

    def run(self, edit):
        savvy_settings = sublime.load_settings("GitSavvy.sublime-settings")
        args = savvy_settings.get("git_graph_args")
        branch_graph = self.git(*args)
        self.view.run_command("gs_replace_view_text", {"text": branch_graph, "nuke_cursors": True})


class GsLogGraphActionCommand(TextCommand, GitCommand):

    """
    Checkout the commit at the selected line.
    """

    def run(self, edit, action):
        self.action = action
        sublime.set_timeout_async(self.run_async, 0)

    def run_async(self):
        selections = self.view.sel()
        if len(selections) != 1:
            return

        lines = util.view.get_lines_from_regions(self.view, selections)
        if not lines:
            return
        line = lines[0]

        commit_hash = line.strip(" /_\|*")[:7]
        if self.action == "checkout":
            self.checkout_ref(commit_hash)
            util.view.refresh_gitsavvy(self.view)
        elif self.action == "view":
            self.view.window().run_command("gs_show_commit", {"commit_hash": commit_hash})

class GsLogGraphMoreInfoCommand(TextCommand, GitCommand):

    """
    Show all info about a commit in a quick panel
    """

    def run(self, edit):
        selections = self.view.sel()
        if len(selections) != 1:
            return

        lines = util.view.get_lines_from_regions(self.view, selections)
        if not lines:
            return
        line = lines[0]

        commit_hash = line.strip(" /_\|*")[:7]
        if (len(commit_hash) <= 3) :
            return

        text = self.git("show", commit_hash, "--format=fuller", "--quiet")
        output_view = self.view.window().create_output_panel("show_commit_info")
        output_view.set_read_only(False)
        output_view.insert(edit, 0, text)
        output_view.set_syntax_file("Packages/GitSavvy/syntax/show_commit.tmLanguage")
        output_view.set_read_only(True)
        self.view.window().run_command("show_panel", {"panel": "output.show_commit_info"})


class GsLogGraphNextCommitCommand(TextCommand, GitCommand):

    """
    move cursor to next commit
    """

    def run(self, edit, forward):
        selections = self.view.sel()
        if len(selections) != 1:
            return

        # command to move one down
        self.view.window().run_command("move", {"by": "lines", "forward": forward})
        lines = util.view.get_lines_from_regions(self.view, selections)
        if not lines:
            return
        line = lines[0]

        commit_hash = line.strip(" /_\|*")[:7]
        if (len(commit_hash) > 3) :
            self.view.window().run_command("gs_log_graph_more_info")
        else :
            self.view.window().run_command("gs_log_graph_next_commit", {"forward": forward})

class GsLogGraphToggleMoreInfoCommand(TextCommand, WindowCommand, GitCommand):

    def run(self, edit):
        savvy_settings = sublime.load_settings("GitSavvy.sublime-settings")

        if (savvy_settings.get("log_graph_view_toggle_more")):
            savvy_settings.set("log_graph_view_toggle_more", False)
        else:
            savvy_settings.set("log_graph_view_toggle_more", True)
        self.view.run_command("gs_log_graph_more_info")
