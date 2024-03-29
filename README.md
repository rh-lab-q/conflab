# conflab

![Confla](logo/confla_icon_BLUE.png?raw=true "Confla")

Conflab aims to be full featured solution for conference management. 

Features:
- easy deployment to OpenShift
- call for papers form
- drag and drop management of schedule 
- export schedule via csv and json
- import of cfp form data from csv


Examples of deployment:
- http://python-conflab.rhcloud.com/oa2015/sched/

Other software for conference planning:
- https://pretalx.com/
- https://github.com/GetTogetherComm/GetTogether/
- https://github.com/openSUSE/osem
- http://indico-software.org/
- http://pentabarf.org/
- TBD judy, symposium, zookeepr, openconferenceware, djep, wafer, funnel, .. https://mail.python.org/pipermail/conferences/2015-August/thread.html
- https://engelsystem.de/index_en.php
- http://frab.github.io/frab/

# Installation
```bash
python3 setup.py install
cd ./wsgi/openshift/
python3 manage.py migrate
python3 manage.py migrate --run-syncdb
python3 manage.py createsuperuser
python3 manage.py runserver
```

# Podman/Docker installation
```
podman build . -t conflab
podman run -p 8000:8000 conflab
# find running container and create admin account
podman exec -it $(podman ps -qf "ancestor=localhost/conflab:latest") bash -c 'cd /code/wsgi/openshift; python ./manage.py createsuperuser'
```
and open http://localhost:8000
