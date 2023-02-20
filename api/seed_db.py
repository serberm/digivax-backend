from app import app, create_roles
from common.seed_database import seed_constants, seed_test_data

app.app_context().push()

create_roles()

seed_constants()
seed_test_data()