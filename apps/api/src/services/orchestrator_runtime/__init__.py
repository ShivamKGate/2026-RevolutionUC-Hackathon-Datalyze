"""
Orchestrator runtime package.

Provides the production pipeline execution engine, adapter contracts,
track profiles, execution policies, and persistence layer.

Integration boundary: this package depends on agent_registry for agent
metadata/DAG but never modifies per-agent specialization internals.
Shivam's specialization modules feed through the AgentExecutionAdapter
contract defined in contracts.py.
"""
