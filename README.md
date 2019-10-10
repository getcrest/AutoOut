# AutoOut

[![Documentation](https://img.shields.io/badge/api-reference-blue.svg)](https://matelabs.github.io/AutoOut/)
[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Mate-Labs-AutoOut/community) 
[![GitHub license](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/MateLabs/AutoOut/blob/master/LICENSE)
[![Status](https://img.shields.io/pypi/status/ansicolortags.svg)](https://github.com/MateLabs/AutoOut)


[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

AutoOut is an automated outlier detection and treatment tool that allows you to get better models with even better accuracy without writing a single line of code.
With it's easy to use and simple interface you can detect and treat outliers in your dataset, that can help improve your final model.

How to Use:
------------

Step 1: Install Dependencies

    pip install -r requirements.txt

Step 2: Make migrations

    python manage.py makemigrations

Step 3: Create tables:

    python manage.py migrate
   
Step 4: Seed the database
    
    python manage.py loaddata app/fixtures/process_statuses.json
    python manage.py loaddata app/fixtures/processes.json

Step 5: Start the server

    python manage.py runserver
    
Step 6: Open the app in your favorite browser
    
    http://127.0.0.1:8000/app/home

Upload your data:
----------------
![upload](https://github.com/MateLabs/AutoOut/blob/master/screenshots/upload.png)

Detect Outliers:
-----------------
![detect](https://github.com/MateLabs/AutoOut/blob/master/screenshots/detect.png)


Treat Outliers:
---------------
![treat](https://github.com/MateLabs/AutoOut/blob/master/screenshots/treat.png)


How to contribute:
-----------------
Step 1: Fork

Step 2: Write your code

Step 3: Create a pull request

Discussion Forum:
-----------------
[Gitter](https://gitter.im/Mate-Labs-AutoOut/community): Forum where all developers can interact with each other. They can discuss the code and approaches there. They can put ask questions to the core team

License
-----------------

[MIT License](https://github.com/MateLabs/AutoOut/blob/master/LICENSE)

[Mate Labs Innovations Pvt Ltd](https://www.matelabs.ai/)