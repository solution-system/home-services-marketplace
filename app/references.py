import secrets


def new_reference():
    # Eight random bytes give a non-sequential reference that is hard to guess.
    return secrets.token_hex(8).upper()
