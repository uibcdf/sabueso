from sabueso._private.argdigest._shared import client


def digest_uniparc_client(uniparc_client, caller=None):
    return client("uniparc_client", uniparc_client, caller)
