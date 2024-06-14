# Troubleshooting

##  Command not found: uvicorn


If you  excecute  `uvicorn app.main:app --host 0.0.0.0 --reload` and if have `Command not found: uvicorn`  

Step 1: verify if uvicorn is installed in the caché
```bash
poetry run which uvicorn 
```
The output should be empty

Step 2 (optional): Remove uvicorn in the project 
```bash
poetry remove uvicorn
```

Step 3: Install uvicorn in the project 
```bash
poetry add uvicorn
```