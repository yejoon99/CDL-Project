docker build -t my-fastapi-app .

docker run -d -p 8000:8000 -v "~/Desktop/cdl_practicum/model and data/fastapi copy/log:/app/logs" --name fastapi-container my-fastapi-app

curl -X POST "http://localhost:8000/inference/" -H "Content-Type: application/json" -d '{"key": "value”}'

cat "~/Desktop/cdl_practicum/model and data/fastapi copy/log/inference_logs.txt"    
