"""Idempotently apply the v0.8.2 empty-model startup fix to local source."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
target = ROOT / "DB-GPT/packages/dbgpt-core/src/dbgpt/model/cluster/worker/manager.py"
text = target.read_text(encoding="utf-8")
marker = "# Model-management endpoints still need a real (initially empty) manager."
if marker in text:
    print("Empty-model startup patch already applied.")
else:
    old = """        _setup_fastapi(worker_params, app, ignore_exception=True, system_app=system_app)
        for llm_deploy_config in models_config.llms:"""
    new = """        _setup_fastapi(worker_params, app, ignore_exception=True, system_app=system_app)
        # The UI and datasource services can run before a model is configured.
        # Model-management endpoints still need a real (initially empty) manager.
        if worker_manager.worker_manager is None:
            worker_manager.worker_manager = _create_local_model_manager(
                worker_params, model_storage
            )
        for llm_deploy_config in models_config.llms:"""
    listener_old = """        worker_manager.after_start(start_listener)
        for embedding_deploy_config in models_config.embeddings:"""
    listener_new = """        # The app listener builds schema embeddings; defer it without embeddings.
        worker_manager.after_start(start_listener if models_config.embeddings else None)
        for embedding_deploy_config in models_config.embeddings:"""
    if text.count(old) != 1 or text.count(listener_old) != 1:
        raise SystemExit("Unexpected upstream source; patch was not applied. Expected DB-GPT v0.8.2.")
    target.write_text(text.replace(old, new).replace(listener_old, listener_new), encoding="utf-8")
    print("Applied empty-model startup patch.")
