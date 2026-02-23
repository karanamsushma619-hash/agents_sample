# Agentic AI Framework Comparison

These frameworks differ primarily in how they handle planning autonomy
versus deterministic control.

------------------------------------------------------------------------

## Core Framework Comparison

  ------------------------------------------------------------------------------------------------------------------------------------------
  Framework   Primary Philosophy    Autonomy      Developer   Orchestration   MCP Support   Recovery       Best Suited For   Tradeoff
                                    Level         Control     Style                         Behavior                         
  ----------- --------------------- ------------- ----------- --------------- ------------- -------------- ----------------- ---------------
  Claude      Autonomous            High          Lower       Model-driven    Native        Built-in       Adaptive          Less
  Agent SDK   orchestration                                   planning loop                 adaptive       assistants,       transparency,
                                                                                            retries &      exploration       less
                                                                                            replanning     agents            deterministic

  LangChain   Composability-first   Medium        High        Prompt +        No native     Must be        RAG, tool-heavy   More glue code
                                                  (manual)    executor driven (adapter      engineered     integrations      
                                                                              needed)       manually                         

  LangGraph   Deterministic state   Low--Medium   Very High   Explicit graph  No native     Designed at    Multi-stage       Higher
              machine                                         (nodes + edges) (adapter      architecture   workflows,        architectural
                                                                              needed)       level          regulated systems complexity

  Google ADK  Structured session    Medium        Medium      Session         Partial /     Structured but Enterprise        Heavier setup
              autonomy                                        lifecycle       structured    bounded        conversational    
                                                              driven                        autonomy       systems           

  OpenAI      Governed tool         Medium        Medium      Model-driven    Via MCP       Schema-based   Production-safe   Schema rigidity
  Agents SDK  execution                                       with strict     server        validation     enterprise        
                                                              schemas         integration                  systems           
  ------------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------

## Strengths & Weaknesses

  -----------------------------------------------------------------------
  Framework               Strengths               Weaknesses
  ----------------------- ----------------------- -----------------------
  Claude Agent SDK        Native MCP, minimal     Less deterministic,
                          integration, strong     opaque reasoning
                          autonomy, built-in      
                          recovery                

  LangChain               Extremely flexible,     No native MCP, glue
                          strong ecosystem, large code required
                          community, strong RAG   
                          support                 

  LangGraph               Deterministic           Higher complexity
                          execution,              
                          state-machine           
                          architecture, strong    
                          traceability            

  Google ADK              Strong session model,   Heavier setup, less
                          structured lifecycle    flexible

  OpenAI Agents SDK       Clean tool system,      Schema rigidity
                          strict schema           
                          enforcement             
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## Autonomy vs Control Positioning

  Framework           Built-in Autonomy   Developer Control   Positioning
  ------------------- ------------------- ------------------- ------------------------------
  Claude Agent SDK    High                Lower               High Autonomy, Lower Control
  LangGraph           Low--Medium         Very High           High Control, Lower Autonomy
  LangChain           Medium              High                High Flexibility & Control
  Google ADK          Medium              Medium              Structured Autonomy
  OpenAI Agents SDK   Medium              Medium              Governed Execution

------------------------------------------------------------------------

## Conceptual Definitions

### High Autonomy

Runtime LLM-driven planning, dynamic tool selection, adaptive recovery.

### Low Autonomy

Predefined execution path with limited runtime improvisation.

### High Control

Explicit state transitions, deterministic execution, auditability.

### Low Control

Model decides flow dynamically.

### Structured Autonomy

Autonomous within defined structural boundaries.

### Governed Execution

Strict tool contracts, schema validation, controlled invocation.

### Flexibility

Ease of integrating tools, APIs, memory layers, and workflows.

------------------------------------------------------------------------

## Standardization Efforts

  -------------------------------------------------------------------------
  Standard            What It Standardizes                   Level
  ------------------- -------------------------------------- --------------
  MCP                 Tool communication interface           Tool-level

  A2A                 Agent-to-agent communication           Agent-level

  Agent Protocol      Structured task delegation and         System-level
                      coordination                           
  -------------------------------------------------------------------------

------------------------------------------------------------------------

## Strategic Summary

Claude optimizes for autonomy.\
LangGraph optimizes for determinism.\
LangChain optimizes for flexibility.\
Google ADK optimizes for structured state.\
OpenAI Agents SDK optimizes for governance.
