import time
from queue_manager import email_queue
from mailer import send_email
from config import MAX_RETRIES


def worker():

    while True:

        job = email_queue.get()

        retries = job.get("retries", 0)

        try:

            send_email(
                job["to"],
                job["subject"],
                job["html"]
            )

        except Exception:

            if retries < MAX_RETRIES:

                job["retries"] = retries + 1
                email_queue.put(job)

            else:

                print("Email permanently failed")

        email_queue.task_done()

        time.sleep(1)
        print("---")
