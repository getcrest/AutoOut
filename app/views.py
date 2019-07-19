import os
import time

import dask
import pandas as pd
from dask import delayed
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from app.models import Dataset, Experiment, Process, ProcessStatus
from app.outlier_treatment.main import detect_all


@csrf_exempt
def home(request):
    return render(request, "home.html")


@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        print(request.FILES)
        all_files = request.FILES.getlist('files[]')
        if len(all_files) > 0:
            try:
                uploaded_file = all_files[0]
                file_name = uploaded_file.name

                filename, file_extension = os.path.splitext(file_name)

                if not file_extension in [".csv", ".h5", '.xlxs']:
                    return JsonResponse({"status": "failure", "message": "No file found"})

                # TODO: Check for file extension here
                if not os.path.exists(settings.MEDIA_ROOT):
                    os.makedirs(settings.MEDIA_ROOT)

                file_name = "{}_{}".format(time.time(), file_name)
                file_path = os.path.join(settings.MEDIA_ROOT, file_name)
                fout = open(file_path, 'wb+')

                # Iterate through the chunks.
                for chunk in uploaded_file.chunks():
                    fout.write(chunk)
                fout.close()

                # Save this file to database
                dataset = Dataset(path=file_name)
                dataset.save()

                return JsonResponse({'status': 'success', 'message': 'Data uploaded successfully',
                                     'file_path': file_name})
            except Exception as e:
                return JsonResponse({'status': 'failure', 'message': 'Error:Upload failed:{}'.format(e)})
        else:
            return JsonResponse({"status": "failure", "message": "No file found"})
    else:
        print(request)
        return JsonResponse({'status': 'failure', 'message': 'Invalid request'})


@csrf_exempt
def detect_outliers(request):
    dataset = Dataset.objects.all().order_by('-created_at')[0]
    file_path = dataset.path

    # Create a detection experiment and start outlier detection
    process = Process.objects.get(name='detection')
    process_status = ProcessStatus.objects.get(name='treatment')
    experiment = Experiment(dataset=dataset, process=process, process_status=process_status)
    experiment.save()

    results = delayed(detect_all)(file_path, experiment.id, settings.RESULTS_ROOT)
    dask.compute(results)

    return JsonResponse({'status': 'success', 'message': 'Detection started successfully'})


@csrf_exempt
def update_process_status(request):
    experiment_id = request.POST.get('experiment_id', None)
    process_id = request.POST.get('process_id', None)
    process_status_id = request.POST.get('process_status_id', None)

    if experiment_id is None or process_id is None or process_status_id is None:
        print("Cannot update status")

    experiment = Experiment.objects.get(pk=experiment_id)
    process_status = ProcessStatus.objects.get(pk=process_status_id)

    experiment.process_status = process_status
    experiment.save()

    return JsonResponse({'status': 'success', 'message': 'Status updated successfully'})


@csrf_exempt
def get_data(request):
    page_no = request.GET.get("page_num", 1)
    print(page_no)
    datasets = Dataset.objects.all().order_by('-created_at')
    latest_dataset = datasets[0]
    dataset_name = latest_dataset.path
    dataset_path = os.path.join(settings.MEDIA_ROOT, dataset_name)
    filename, file_extension = os.path.splitext(dataset_path)

    if file_extension == '.csv':
        df = pd.read_csv(dataset_path)
        df = df.iloc[(page_no-1)*20:(page_no-1)*20+19, :]

    print(df)

    return JsonResponse(df.to_json(orient='records'), safe=False)
