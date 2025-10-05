from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

class TokenRequest(BaseModel):
    user_id: str
    expires_hours: int = 24

@app.get("/healthz")
async def health():
    return {"status": "ok", "timestamp": int(time.time())}

@app.get("/readyz")
async def ready():
    return {"status": "ready", "timestamp": int(time.time())}

@app.post("/ask")
async def ask(request: QuestionRequest):
    # Mock response with some delay to simulate thinking
    question = request.question
    
    # Generate a mock response
    response = f"""I understand you're asking about: "{question}"

This is a **mock response** from the LIQUID HIVE 25 system. In production, this would use:

1. **Self-Loop Reasoning**: Plan → Draft → Critic → Revise cycles
2. **Multi-Tier Models**: Intelligent failover between local vLLM and remote APIs
3. **Hybrid RAG**: Dual indexing with Qdrant vectors + Elasticsearch BM25

## Example Code Block

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate fibonacci of 10
print("Fibonacci(10) = 55")
```

## Key Features

- ✅ Iterative reasoning with verification
- ✅ Context-aware responses
- ✅ Code execution sandbox
- ✅ Mathematical verification

Feel free to ask me anything else!"""
    
    return {"answer": response}

@app.post("/auth/token")
async def create_token(request: TokenRequest):
    # Mock token generation
    token = f"mock_token_{request.user_id}_{int(time.time())}"
    return {"token": token}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
