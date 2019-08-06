import json
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
from app.outlier_treatment.main import detect_all, get_final_outliers, treat


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
    process = Process.objects.get(name='Detection')
    process_status = ProcessStatus.objects.get(name='Running')
    experiment = Experiment(dataset=dataset, process=process, process_status=process_status)
    experiment.save()
    results = delayed(detect_all)(os.path.join(settings.MEDIA_ROOT, file_path), experiment.id, settings.RESULTS_ROOT)
    dask.compute(results)

    return JsonResponse({'status': 'success', 'message': 'Detection started successfully', 'experiment_id': experiment.id})


@csrf_exempt
def update_experiment_status(request):
    experiment_id = request.POST.get('experiment_id', None)
    process_status_id = request.POST.get('process_status_id', None)
    results_file_path = request.POST.get('results_file_path', None)
    treated_file_path = request.POST.get('treated_file_path', None)

    if experiment_id is None or process_status_id is None:
        print("Cannot update status")

    experiment = Experiment.objects.get(pk=experiment_id)
    process_status = ProcessStatus.objects.get(pk=process_status_id)

    experiment.process_status = process_status
    if results_file_path is not None:
        experiment.results_path = results_file_path

    if treated_file_path is not None:
        experiment.treated_file_path = treated_file_path
        
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
        df = df.iloc[(page_no - 1) * 20:(page_no - 1) * 20 + 19, :]
        return JsonResponse(df.to_json(orient='records'), safe=False)


@csrf_exempt
def get_outliers(request):
    experiment_id = request.POST.get("experiment_id")

    if experiment_id is None:
        return JsonResponse({"status": "success", "message": 'Experiment id is missing'})

    experiment = Experiment.objects.get(pk=experiment_id)
    results_file_path = os.path.join(settings.RESULTS_ROOT, experiment.results_path)

    if experiment.process_status_id == 2:
        return JsonResponse({'status': 'success', 'message': 'Experiment is still running. Please wait for sometime'})

    try:
        with open(results_file_path, "r") as fp:
            outliers = json.load(fp)
            final_outliers = get_final_outliers(outliers)
            return JsonResponse({"status": "success", "outliers": final_outliers})
    except Exception as e:
        print("Exception:", e)
        return JsonResponse({'status': "failure", "message": "Error"})


@csrf_exempt
def treat_outliers(request):
    request_obj = json.loads(request.body.decode("utf-8"))
    experiment_id = request_obj["experiment_id"]

    if experiment_id is None:
        return JsonResponse({"status": "success", "message": 'Experiment id is missing'})

    experiment = Experiment.objects.get(pk=experiment_id)
    results_file_path = os.path.join(settings.RESULTS_ROOT, experiment.results_path)

    if experiment.process_status_id == 2:
        return JsonResponse({'status': 'success', 'message': 'Experiment is still running. Please wait for sometime'})

    try:
        with open(results_file_path, "r") as fp:
            outliers = json.load(fp)
            final_outliers = get_final_outliers(outliers)

            process = Process.objects.get(name='Treatment')
            process_status = ProcessStatus.objects.get(name='Running')
            experiment2 = Experiment(dataset=experiment.dataset, process=process, process_status=process_status)
            experiment2.save()

            results = delayed(treat)(os.path.join(settings.MEDIA_ROOT, experiment2.dataset.path),
                                     final_outliers, experiment2.id, settings.MEDIA_ROOT)
            dask.compute(results)

            return JsonResponse(
                {"status": "success", "message": "Outlier treatment started", "experiment_id": experiment2.id})
    except Exception as e:
        print("Exception:", e)
        return JsonResponse({'status': "failure", "message": "Error"})


@csrf_exempt
def get_experiment_status(request):
    if request.method == 'POST':
        # experiment_id = request.POST.get("experiment_id")
        request_obj = json.loads(request.body.decode("utf-8"))
        experiment_id = request_obj["experiment_id"]

        if experiment_id is None:
            return JsonResponse({"status": "success", "message": 'Experiment id is missing'})

        experiment = Experiment.objects.get(pk=experiment_id)

        return JsonResponse({"status":"success", "experiment_status": experiment.process_status.name})
    else:
        return JsonResponse({'status': "failure", "message": "Invalid request"})