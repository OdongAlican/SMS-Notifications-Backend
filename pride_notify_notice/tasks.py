from celery import shared_task

@shared_task
def retrieve_data():
    # Operations
    lst = [1, 2, 3, 4, 5, 6, 7]
    for number, index in enumerate(lst):
        print(f"{number}: {index}")
    return "done"


"""
This is used to handle a scenario where the task might fail to excute then we can set a retry after a minute (60 seconds)

@shared_task(bind=True)
def my_task(self):
    try:
        # Do something that might fail
    except SomeError:
        raise self.retry(countdown=60)
"""
