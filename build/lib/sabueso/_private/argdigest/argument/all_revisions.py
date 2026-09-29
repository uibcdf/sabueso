from sabueso._private.argdigest._shared import boolean


def digest_all_revisions(all_revisions, caller=None):
    return boolean("all_revisions", all_revisions, caller)
