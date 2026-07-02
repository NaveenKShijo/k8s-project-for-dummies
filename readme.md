To deploy the Microservice architechture in local machine, manually handling containers,
Just run: 
    docker compose up -d 


To deploy this architecture in K8s cluster:
    kubectl apply -R -f k8s/

    Commands to run to check whether applciation running:
        kubectl get deployments
        kubectl get pods       
    
    Responses:
        docker exec -it firstcluster-control-plane curl http://localhost:30801/hello
            {"Message":"This is User page"}

        docker exec -it firstcluster-control-plane curl http://localhost:30800/hello
            {"Message":"This is Orders page"}
    
    Problem & improvement:
        docker exec -it firstcluster-control-plane curl http://localhost:30800/users
            Internal Server Error

        Uncomment the register code for K8s and comment the line for docker compose in both 'orders.py' & 'users.py'. Create images for both and load them into cluster and update the deployment.yaml manifests of both to solve the above problem of communication between 2 microservices.
        