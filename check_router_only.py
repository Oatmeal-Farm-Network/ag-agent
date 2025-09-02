# Save as: check_router_only.py
# Purpose: Print ONLY the router's selected specialist(s) and rationale for each prompt (no agent answers).

import asyncio
import json

from autogen_module.routeagents import AgentRouter

TEST_PROMPTS = [
    # Declaratives vs advice
    "I have 5 sheep",
    "We keep around 12 goats on pasture",
    "My soil pH is 7.2",
    "What did I say my herd size is?",

    # Pure greetings / general
    "Hi there!",
    "Okay, continue",
    "Summarize what we discussed today",

    # CRUD (profile/contact fields without 'People' prefix)
    "Set my Email to alice@example.com",
    "Change my UserName to rancher_42",
    "Show my profile info",
    "Delete my Bio",

    # Single-domain advice/questions
    "My soil pH is 8.0; how do I lower it?",
    "Field is waterlogged—how can I improve drainage?",
    "Leaves are yellowing—recommend NPK and schedule",
    "Should I do foliar feeding on tomatoes this week?",
    "Will it rain in 94542 tomorrow?",
    "Forecast for Austin, TX this weekend for spraying?",
    "Best sheep breed for hot, humid climates?",
    "Feeding plan for 2‑month‑old lambs in summer?",

    # Multi-topic (2 agents)
    "Change my Email to bob@example.com and suggest a fertilizer plan",
    "Soil is alkaline—should I irrigate given tomorrow’s forecast?",
    "Heavy rain forecast—should I apply fertilizer now?",

    # Multi-topic (potentially 3 agents)
    "My soil is acidic and leaves show potassium deficiency; recommend amendments and an NPK schedule for the week",
]

async def route_only(router: AgentRouter, prompt: str):
    # Call the router LLM directly to get {agents, why} without executing specialists
    resp = router.router_agent.generate_reply([{
        "role": "user",
        "content": f"Which specialist is needed for: {prompt}"
    }])
    try:
        parsed = json.loads(str(resp).strip())
        if isinstance(parsed, dict):
            agents = parsed.get("agents") or []
            why = parsed.get("why") or ""
        elif isinstance(parsed, list):
            agents = parsed
            why = ""
        else:
            agents, why = [], ""
    except Exception:
        agents, why = [], ""
    # Fallback to router method if needed
    if not agents:
        sel = await router._route_specialist(prompt)
        if isinstance(sel, str):
            sel = [sel]
        agents = sel
    return {"query": prompt, "agents": agents, "why": why}

async def main(prompts):
    router = AgentRouter()
    results = []
    for p in prompts:
        try:
            results.append(await route_only(router, p))
        except Exception as e:
            results.append({"query": p, "agents": ["<error>"], "why": str(e)})
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main(TEST_PROMPTS))
