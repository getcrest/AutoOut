from app.celery import app


@app.task(bind=True)
def train():


    pass
