import time

last_sent = {}


def can_send(email, delay):
    now = time.time()

    if email in last_sent:
        if now - last_sent[email] < delay:
            return False

    last_sent[email] = now
    return True
