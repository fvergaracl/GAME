# Deploying GAME on Kubernetes ☸️

This guide explains how to deploy the GAME project on a Kubernetes cluster. Kubernetes provides a scalable and robust platform for running containerized applications in a production environment.

## Prerequisites

Before deploying GAME to Kubernetes, ensure you have the following:

- A Kubernetes cluster (e.g., Google Kubernetes Engine (GKE), Amazon EKS, Azure AKS, or a local cluster such as Minikube).
- `kubectl` installed and configured to access your cluster.
- Docker installed on your local machine (to build images if needed).
- Kubernetes configuration files for the project (found in the `k8s/` directory).



## Step-by-step Deployment

### 1. Build and Push the Docker Image

First, ensure that the Docker image of your application is available to the Kubernetes cluster. You can build the Docker image locally and push it to a container registry like Docker Hub or Google Container Registry (GCR).

1. **Build the Docker image**:

   ```bash
   docker build -t <your-docker-username>/game:latest .
   ```

2. **Push the image to a container registry**:

   ```bash
   docker push <your-docker-username>/game:latest
   ```

   Replace `<your-docker-username>` with your Docker Hub username or the appropriate registry details.

### 2. Set Up Kubernetes Manifests

The `kubernetes/` directory is organized into subdirectories for different types of Kubernetes resources. Each subdirectory contains the necessary YAML configuration files to deploy the GAME application. Ensure you have the following files:

- **ConfigMaps** (`configmaps/`):
  - `env-prod-configmap.yaml`: Defines environment variables used by the application in production.

- **Deployments** (`deployments/`):
  - `gamificationengine-deployment.yaml`: Defines the Deployment for the GAME application, including the container image, replicas, and environment settings.
  - `postgres-deployment.yaml`: Defines the Deployment for the PostgreSQL database.

- **Services** (`services/`):
  - `gamificationengine-service.yaml`: Service to expose the GAME application internally within the cluster.
  - `postgres-service.yaml`: Service to expose the PostgreSQL database.

- **Ingresses** (`ingresses/`):
  - `ingress.yaml`: Ingress resource to route external HTTP(S) traffic to the GAME application (optional, for external access).

- **Volume** (`volumen/`):
  - `postgres-data-persistentvolumeclaim.yaml`: Defines a PersistentVolumeClaim to ensure PostgreSQL data is stored persistently.

### 3. Apply the Kubernetes Resources

Navigate to each relevant subdirectory (`configmaps/`, `deployments/`, `services/`, `ingresses/`, `volumen/`) and apply the configuration files to your Kubernetes cluster using `kubectl`:

```bash
kubectl apply -f configmaps/env-prod-configmap.yaml
kubectl apply -f volumen/postgres-data-persistentvolumeclaim.yaml
kubectl apply -f deployments/postgres-deployment.yaml
kubectl apply -f deployments/gamificationengine-deployment.yaml
kubectl apply -f services/postgres-service.yaml
kubectl apply -f services/gamificationengine-service.yaml
kubectl apply -f ingresses/ingress.yaml  # Optional, if you are using Ingress for external access
```


### 4. Verify Deployment

Check that the pods are running and services are correctly exposed:

```bash
kubectl get pods
kubectl get services
```

You should see both the PostgreSQL and GAME application pods in a `Running` state.

### 5. Access the Application

If you set up an Ingress, you can access the application using the domain you've mapped to your ingress IP.

For NodePort, access the application at `<node-ip>:<node-port>`.

## Scaling the Application

Kubernetes allows easy scaling of your application. To scale the number of GAME application instances, run:

```bash
kubectl scale deployment game-deployment --replicas=3
```

This will increase the number of pods running the GAME application to 3, ensuring better load distribution.


## Monitoring the Deployment

Monitor the state of your deployments, services, and pods using `kubectl` commands:

- View all pods:

  ```bash
  kubectl get pods
  ```

- Describe a specific pod for more detailed information:

  ```bash
  kubectl describe pod <pod-name>
  ```

- Check logs of a specific pod:

  ```bash
  kubectl logs <pod-name>
  ```


## Rolling Updates and Rollbacks

Kubernetes supports rolling updates, ensuring zero downtime when updating your application.

### Performing a Rolling Update

1. Build and push a new Docker image with the updated code:

   ```bash
   docker build -t <your-docker-username>/game:v2 .
   docker push <your-docker-username>/game:v2
   ```

2. Update the `game-deployment.yaml` to reference the new image version:

   ```yaml
   spec:
     containers:
     - name: game-container
       image: <your-docker-username>/game:v2
   ```

3. Apply the updated deployment:

   ```bash
   kubectl apply -f game-deployment.yaml
   ```

Kubernetes will perform a rolling update, gradually replacing old pods with the new ones.

### Rolling Back

If something goes wrong with the update, you can easily rollback to the previous version:

```bash
kubectl rollout undo deployment/game-deployment
```

By following this guide, you should be able to deploy and manage the GAME application on a Kubernetes cluster. Kubernetes offers powerful features such as auto-scaling, rolling updates, and self-healing that make it an ideal platform for running production workloads.
