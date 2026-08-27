# ForensiDrive architecture

ForensiDrive is a graphical control layer for SystemRescue. It is not a custom Linux distribution, display server, or window manager.

## Layers

1. **UI** (`app/ui`, `app/modules`) — Tkinter screens and wording for non-technical users.
2. **Core** (`app/core`) — storage discovery, process execution, errors, system facts.
3. **Integrations** (`app/integrations`) — SystemRescue detection and tool adapters.
4. **Models** (`app/models`) — drive, partition, and operation records.

The GUI never builds large subprocess command lines. Adapters detect whether a tool exists, then return an argument list. `core.commands` and `core.process` run those lists with `shell=False`.

## Runtime layout

The project is portable. The install root is the directory that contains `app/`, not a hard-coded home path.

- Development: the Git checkout
- Live target: `/usr/local/forensidrive/`
- Override: `FORENSIDRIVE_ROOT`

Launch:

```
python3 app/main.py
```

## Safety

Erasure requires drive identity, repeated confirmation, typed device path, and available-tool detection. Recovery writes to a user-chosen folder and uses existing SystemRescue utilities only.

## Deferred

Audit, authentication, encrypted audit partitions, evidence databases, and user accounts are out of scope for this prototype.
