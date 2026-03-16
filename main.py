from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from dependencies import conversation_service, pipeline_service, reply_suggestion_service
from models import (
    AddMessageRequest,
    AddMessageResponse,
    RunPipelineRequest,
    SuggestedReply,
    UpdateTaskStatusRequest,
    WorkspaceData,
)
from state import store

app = FastAPI(title="DealFlow AI", version="0.1.0")
allowed_origins = [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/clients")
def list_clients():
    return conversation_service.list_clients()


@app.get("/clients/{client_id}/conversation")
def get_client_conversation(client_id: str):
    try:
        return conversation_service.get_conversation(client_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/clients/{client_id}/workspace", response_model=WorkspaceData)
def get_client_workspace(client_id: str):
    try:
        client = conversation_service.get_client(client_id)
        conversation = conversation_service.get_conversation(client_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    pipeline_result = store.recommendations.get(client_id)
    tasks = [task for task in store.tasks if task.client_id == client_id]
    return WorkspaceData(
        client=client,
        conversation=conversation,
        pipeline_result=pipeline_result,
        tasks=tasks,
        suggested_replies=reply_suggestion_service.suggest(
            client=client,
            conversation=conversation,
            pipeline_result=pipeline_result,
            tasks=tasks,
        ),
    )


@app.post("/messages", response_model=AddMessageResponse)
def add_message(request: AddMessageRequest):
    try:
        event = conversation_service.add_message(request)
        pipeline_result = pipeline_service.run(request.client_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AddMessageResponse(
        status="message_added",
        event=event,
        workspace=WorkspaceData(
            client=conversation_service.get_client(request.client_id),
            conversation=conversation_service.get_conversation(request.client_id),
            pipeline_result=pipeline_result,
            tasks=[task for task in store.tasks if task.client_id == request.client_id],
            suggested_replies=reply_suggestion_service.suggest(
                client=conversation_service.get_client(request.client_id),
                conversation=conversation_service.get_conversation(request.client_id),
                pipeline_result=pipeline_result,
                tasks=[task for task in store.tasks if task.client_id == request.client_id],
            ),
        ),
    )


@app.post("/pipeline/run", response_model=WorkspaceData)
def run_pipeline(request: RunPipelineRequest):
    try:
        pipeline_result = pipeline_service.run(request.client_id)
        return WorkspaceData(
            client=conversation_service.get_client(request.client_id),
            conversation=conversation_service.get_conversation(request.client_id),
            pipeline_result=pipeline_result,
            tasks=[task for task in store.tasks if task.client_id == request.client_id],
            suggested_replies=reply_suggestion_service.suggest(
                client=conversation_service.get_client(request.client_id),
                conversation=conversation_service.get_conversation(request.client_id),
                pipeline_result=pipeline_result,
                tasks=[task for task in store.tasks if task.client_id == request.client_id],
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/clients/{client_id}/reply-suggestions", response_model=list[SuggestedReply])
def get_reply_suggestions(client_id: str):
    try:
        client = conversation_service.get_client(client_id)
        conversation = conversation_service.get_conversation(client_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    pipeline_result = store.recommendations.get(client_id)
    tasks = [task for task in store.tasks if task.client_id == client_id]
    return reply_suggestion_service.suggest(
        client=client,
        conversation=conversation,
        pipeline_result=pipeline_result,
        tasks=tasks,
    )


@app.get("/tasks")
def get_tasks():
    return store.tasks


@app.get("/recommendations")
def get_recommendations():
    return list(store.recommendations.values())


@app.patch("/tasks/{task_id}")
def update_task_status(task_id: str, request: UpdateTaskStatusRequest):
    try:
        return store.update_task_status(task_id, request.status)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/admin/reset")
def reset_state():
    store.reset()
    return {"status": "reset"}
