# WASMBOX Architecture

## 1. Overview

WASMBOX is a secure, lightweight WebAssembly-based execution
environment for running untrusted Python plugins in a multi-tenant
SaaS environment.

## 2. Core Components

WASMBOX consists of:

1. Developer Portal
2. API Layer
3. Execution Orchestrator
4. Python-to-WASM Compiler
5. WASM Sandbox
6. Security/Capability Manager
7. Resource Manager
8. Multi-Tenancy Manager
9. Host Function Layer
10. Metrics and Monitoring

## 3. Execution Flow

Developer
→ Developer Portal
→ API
→ Orchestrator
→ Compiler
→ WASM Sandbox
→ WASM Runtime
→ Execution
→ Metrics
→ API
→ Developer Portal

## 4. Module Ownership

| Module | Owner |
|---|---|
| Architecture & Orchestrator | Team Lead |
| WASM Compiler | Member 2 |
| Sandbox & Security | Member 3 |
| Multi-Tenancy & Resources | Member 4 |
| Developer Portal | Member 5 |

## 5. Security Principles

- Untrusted code must execute inside the WASM sandbox.
- Host access is deny-by-default.
- Filesystem access must be restricted.
- Network access must be restricted.
- Resource limits must be enforced.
- Tenant resources must be isolated.
- Host functions must require explicit capabilities.

## 6. Execution States

CREATED
→ COMPILING
→ READY
→ RUNNING
→ SUCCESS

Possible failure states:

- COMPILATION_FAILED
- EXECUTION_FAILED
- TIMEOUT
- MEMORY_LIMIT
- INSTRUCTION_LIMIT
- PERMISSION_DENIED
- SANDBOX_ERRORgit status