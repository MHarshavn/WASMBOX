# WASMBOX Capability-Based Access

## Principle

WASMBOX uses capability-based access control for host functionality.

A plugin must explicitly possess a capability before it can perform
the corresponding host operation.

## Default Policy

All capabilities are denied unless explicitly granted.

## Capability Names

The initial capability namespace includes:

- `host.log`
- `filesystem.read`
- `filesystem.write`
- `network.connect`

## Example

A plugin granted:

`host.log`

may use the logging host function.

It must not automatically receive:

- `filesystem.read`
- `filesystem.write`
- `network.connect`

## Authorization Flow

```text
Plugin
  |
  v
Request Host Operation
  |
  v
Capability Checker
  |
  +---- Capability Granted ----> Execute Operation
  |
  +---- Capability Missing ----> DENY