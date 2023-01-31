# Digivax Enterprise API layer

# Build development docker images

## Build the AWS Linux docker image with necessary packages
navigate to repo root directory:    

    docker build -t de_api:latest .

## Run a dev mysql server using Docker
```
docker run --name dev_de_db -e "MYSQL_ROOT_PASSWORD=1234" -e "MYSQL_DATABASE=de" --publish 3306:3306   -d mysql:latest --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci

```

# Run development environment
navigate to repo root directory:

	docker start dev_de_db

Windows

	docker run -it -v %cd%:/home --entrypoint "bash" -p 5000:5000 --rm -e SECRET_KEY=12345 -e FLASK_APP=/home/api/run.py -e FLASK_ENV=developent de_api:latest

Linux

	docker run -it -v $(pwd):/home --entrypoint "bash" -p 5000:5000 --rm -e SECRET_KEY=12345 -e FLASK_APP=/home/api/run.py -e FLASK_ENV=developent de_api:latest

# First run
to set up database type at the docker bash terminal

```bash
export FLASK_APP=/home/api/app.py
export FLASK_ENV=development
```

```bash
flask db upgrade
cd api
python3.8 seed_db.py
```

# Run application
Run a dev server accessible on localhost:

	flask run --host 0.0.0.0

# Application details

## Database seeds
User roles, various constants, and surrogate data and accounts are loaded into the database when a request is first made to the server.

The test accounts are as follows:
##### Orgs
- Towers
- North High
- Subway

##### Test Accounts
- <fname> <lname> (<fname>-<lname>@dvt.com:1234) fname indicates org, lname indicates role
- towers super (towers-super@dvt.com:1234) super-admin and owner at Towers
- northhigh super (northhigh-super@dvt.com:1234) super-admin and owner at North High
- subway super (subway-super@mydvt.com:1234) super-admin and owner at Subway
- subway admin ...
- subway employee
- towers employee
- de super
- de collector

## API Endpoint Documentation
See https://documenter.getpostman.com/view/9802924/TzskD3NY

## To manually run python scripts in the app context:

```bash
cd api
```

```python
import app
from common.seed_database import seed_constants, seed_test_data
app.app.app_context.push()
...
```

## Production Test Account
org: TestOrg
link: testorg
admin: testorg-admin@dvt.com 1234
collector1: defaulttestorg-collector1@dvt.com 1234 (for testing functionality where org collectors only see their team)
collector2: defaulttestorg-collector2@dvt.com 1234

## transfering old s3 to new s3
set AWS_PROFILE=tflab
aws s3 sync s3://tflabs-s3/scans/ s3://dve-s3-prod/scans/


## User Roles
- org_super_admin: can create other org admins and users
- org_admin: can see organization level dashboards
- org_employee: can see their own card and download to apple wallet
- org_collector: can check in employees in their org for testing/vaccine verification
- de_super_admin: access to all orgs, can create org super users, admins, and employees
- de_collector: can check in employees across all orgs for testing/vaccine verifications
  
