---
name: obs:trace
description: Show the endpoint trace map — static call-tree visualization of all @observable endpoint functions and their nested call chains.
argument-hint: "[path]"
allowed-tools:
  - Bash
  - Read
---

# Endpoint Trace Map

Display the static call-tree for all functions tagged `@observable(tags=["endpoint"])`.

## Steps

1. Determine the target path:
   - If `$ARGUMENTS` is provided, use it
   - Otherwise, default to `./src`

2. Run the trace map:
   ```bash
   python hooks/post_edit_check.py $TARGET
   ```

3. The output shows:
   - Total functions and compliance rate
   - Number of traced endpoints
   - For each endpoint: the full nested call tree with tags

   Example output:
   ```
   Endpoint traces:
     -> calculate  [endpoint, critical]
       -> compute  [transform]
       -> parse_input  [transform]
       -> validate_operation  [transform]
   ```

4. If there are gaps in the trace (functions called by endpoints that are not @observable), flag them and suggest adding the decorator.
