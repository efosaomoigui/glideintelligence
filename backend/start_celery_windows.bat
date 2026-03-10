@echo off
echo Starting Celery Worker for Windows...
echo Using --pool=solo to avoid multiprocessing/asyncio hangs on Windows.
python -m celery -A app.workers.celery_app worker --pool=solo --loglevel=info
