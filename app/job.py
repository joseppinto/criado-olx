from apscheduler.schedulers.blocking import BlockingScheduler
import requests


def job():
    requests.get(url='https://criado-olx.herokuapp.com/update')


# Create an instance of scheduler and add function.
scheduler = BlockingScheduler()
scheduler.add_job(job, "interval", seconds=60)
scheduler.start()