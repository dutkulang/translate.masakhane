Core implementation of translate.masakhane

## How to run the project

With the project in it's final stage excepted to be serverless,

These implementations are for development purposes only

Create and activate virtual environment
```sh
# for linux (debian/ubuntu)
python3 -m venv .venv ; source .venv/bin/activate
```
`Not tested on windows`

```sh
pip install -r requirements.txt
```

start the project 

```sh
uvicorn main:app --reload --port 8000
```


### Available endpoints

`/languages` [GET] returns json of languages current under implementation 

`/health` : [GET] Returns json with site status

`/translate` : [POST] excepts JSON object

```json
{
    "text": "Hello, how are you today?",
    "source_lang": "en", # Default source language 
    "target_lang": "lg" # luganda
}
```
## Run tests

```sh
# run tests
pytest -v tests/
```
