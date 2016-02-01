# conflab

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
- https://github.com/openSUSE/osem
- http://indico-software.org/
- http://pentabarf.org/

# Installation
```bash
python3 setup.py install
cd ./wsgi/openshift/
python3 manage.py syncdb
python3 manage.py runserver
```

