from apscheduler.schedulers.blocking import BlockingScheduler
import requests
import os


def job():
    requests.get(url=os.environ["UPDATE_URL"])


# Create an instance of scheduler and add function.
scheduler = BlockingScheduler()
scheduler.add_job(job, "interval", seconds=60)
scheduler.start()