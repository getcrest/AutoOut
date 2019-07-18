import glob
import json
import os
import time

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import pandas as pd

from app.models import Dataset


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

                return JsonResponse({'status': 'success', 'message': 'Image uploaded successfully',
                                     'file_path': file_name})
            except Exception as e:
                return JsonResponse({'status': 'failure', 'message': 'Error:Upload failed:{}'.format(e)})
        else:
            return JsonResponse({"status": "failure", "message": "No file found"})
    else:
        print(request)
        return JsonResponse({'status': 'failure', 'message': 'Invalid request'})


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
