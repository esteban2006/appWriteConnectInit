from queue import Queue

email_queue = Queue()


def add_email_job(job):
    email_queue.put(job)
