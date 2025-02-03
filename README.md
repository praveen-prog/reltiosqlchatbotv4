conda create -n sqlbotenv

conda activate sqlbotenv

pip install -r requirements.txt

cd src
run python app.py

Note: Wheneve new table is added,helper.py need to be added with that table name for query.