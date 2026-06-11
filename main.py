from fastapi import FastAPI, HTTPException

from schemas import AnalyzeRequest, AnalyzeResult, DiagnosePodRequest
from prompts import build_log_analysis_prompt
from llm_client import analyze_logs_with_llm

from agent import diagnose_pod_with_tools


app = FastAPI(
    title="AI Ops Assistant",
    description="A minimal AI-powered Kubernetes log analysis assistant.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResult)
def analyze_logs(request: AnalyzeRequest):
    try:
        prompt = build_log_analysis_prompt(
            context=request.context,
            logs=request.logs,
        )
        result = analyze_logs_with_llm(prompt)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    

@app.post("/diagnose-pod", response_model=AnalyzeResult)
def diagnose_pod(request: DiagnosePodRequest):
    try:
        result = diagnose_pod_with_tools(
            namespace=request.namespace,
            pod_name=request.pod_name,
            context=request.context,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))