# MAgent4Science

Team 17: MAGA (Make Agents Great Again)
- Basia Koch
- Baron Gracias
- Felix Burton
- Fred Lawrence
- Harvey Bermingham

## Backend

Runtime code now lives in `backend/`:

- `backend/agents/` contains one markdown prompt file per pipeline agent.
- `backend/tools/` contains literature API helpers and caching.
- `backend/pipeline.py` contains the LangGraph orchestration.
- `backend/run.py` is the backend CLI entrypoint.

Run the demo with:

```bash
python run.py "my hypothesis text"
```

When swapping in real agent implementations, add `backend/agents/<agent_name>.py`
and export either `<agent_name>(state)` or `run(state)`.
