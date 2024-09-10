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

## Token expired

If you have a token expired problem, you have 2 options

1) Just log out and login again
2) **(Best way)** In the identity and access management (**Keycloak** in this case) you must change the setting related with the **Access Token Lifespan** . In keycloak, first select the realm that contains your client, then click over "Clients" and select your client , after that select the "Advance" tab an chage the options of **Access Token Lifespan** to the desired time