#!/bin/bash

flask db upgrade
cd /home/api
python3.8 seed_db.py
