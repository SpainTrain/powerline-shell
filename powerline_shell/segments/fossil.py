import os
import subprocess
from ..utils import RepoStats, ThreadedSegment


def get_PATH():
    """Normally gets the PATH from the OS. This function exists to enable
    easily mocking the PATH in tests.
    """
    return os.getenv("PATH")


def fossil_subprocess_env():
    return {"PATH": get_PATH()}


def _get_fossil_branch():
    branches = os.popen("fossil branch 2>/dev/null").read().strip().split("\n")
    return ''.join([
        i.replace('*','').strip()
        for i in branches
        if i.startswith('*')
    ])


def parse_fossil_stats(status):
    stats = RepoStats()
    for line in status:
        if line.startswith("ADDED"):
            stats.staged += 1
        elif line.startswith("EXTRA"):
            stats.new += 1
        elif line.startswith("CONFLICT"):
            stats.conflicted += 1
        else:
            stats.changed += 1
    return stats


def build_stats():
    try:
        subprocess.Popen(['fossil'], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         env=fossil_subprocess_env()).communicate()
    except OSError:
        # Popen will throw an OSError if fossil is not found
        return (None, None)
    branch = _get_fossil_branch()
    if branch == "":
        return (None, None)
    changes = os.popen("fossil changes 2>/dev/null").read().strip().split("\n")
    extra = os.popen("fossil extras 2>/dev/null").read().strip().split("\n")
    extra = ["EXTRA " + filename for filename in extra]
    if changes == extra == ['']:
        return (RepoStats(), branch)
    status = [line for line in changes + extra if line != '']
    stats = parse_fossil_stats(status)
    return stats, branch


class Segment(ThreadedSegment):
    def run(self):
        self.stats, self.branch = build_stats()

    def add_to_powerline(self):
        self.join()
        if not self.stats:
            return
        bg = self.powerline.theme.REPO_CLEAN_BG
        fg = self.powerline.theme.REPO_CLEAN_FG
        if self.stats.dirty:
            bg = self.powerline.theme.REPO_DIRTY_BG
            fg = self.powerline.theme.REPO_DIRTY_FG

        self.powerline.append(" " + self.branch + " ", fg, bg)
        self.stats.add_to_powerline(self.powerline)
