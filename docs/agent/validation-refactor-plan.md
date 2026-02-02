# Agent Validation Module Refactoring Plan

## Overview

The `agent/src/lib/validation.py` file has grown to 429 lines and handles multiple distinct responsibilities. This plan outlines how to split it into focused, maintainable modules.

---

## Current State Analysis

### File Statistics
- **Location**: `agent/src/lib/validation.py`
- **Size**: 429 lines
- **Responsibilities**: 4 distinct domains

### Current Structure

```
validation.py (429 lines)
├── Command Validation (Lines 17-355)
│   ├── CommandAllowlistEntry dataclass
│   ├── COMMAND_ALLOWLIST constant (17 entries)
│   ├── CommandValidator class
│   └── validate_command() function
│
├── Docker Run Validation (Lines 27-137)
│   ├── BLOCKED_DOCKER_RUN_FLAGS constant
│   ├── validate_docker_run_command() function
│   └── Flag/capability/namespace checking
│
├── Volume Validation (Lines 46-173, 369-383)
│   ├── BLOCKED_VOLUME_PATTERNS constant
│   ├── PROTECTED_PATHS constant
│   └── _validate_volume_mount() function
│
└── Docker Params Validation (Lines 358-429)
    ├── BLOCKED_DOCKER_PARAMS constant
    └── validate_docker_params() function
```

### Dependencies (What Imports This)

| File | Imports |
|------|---------|
| `lib/__init__.py` | All public exports |
| `security.py` | `validate_command`, `validate_docker_params`, constants |
| `tests/test_security.py` | Multiple validators and constants |
| `tests/test_validation_extended.py` | All validators and constants |

### Exported API (Must Maintain)

```python
# Classes
CommandValidator
CommandAllowlistEntry

# Functions
validate_command
validate_docker_params
validate_docker_run_command

# Constants
COMMAND_ALLOWLIST
BLOCKED_DOCKER_PARAMS
BLOCKED_DOCKER_RUN_FLAGS
BLOCKED_VOLUME_PATTERNS
PROTECTED_PATHS
```

---

## Proposed Structure

### New Module Layout

```
agent/src/lib/
├── validation/                    # NEW: Package directory
│   ├── __init__.py               # Public API exports
│   ├── constants.py              # Shared constants (~60 lines)
│   ├── command_validation.py     # Command allowlist & validator (~180 lines)
│   ├── docker_validation.py      # Docker run/params validation (~120 lines)
│   └── volume_validation.py      # Volume mount validation (~70 lines)
│
├── __init__.py                   # Update imports
└── ... (other modules unchanged)
```

### Module Responsibilities

#### 1. `validation/constants.py` (~60 lines)
Shared security constants used across validators.

```python
# Contents:
- BLOCKED_DOCKER_RUN_FLAGS: Set[str]
- BLOCKED_VOLUME_PATTERNS: List[str]
- PROTECTED_PATHS: List[str]
- BLOCKED_DOCKER_PARAMS: Dict[str, Any]
```

#### 2. `validation/volume_validation.py` (~70 lines)
Volume mount security validation.

```python
# Contents:
- _validate_volume_mount(volume_spec: str) -> bool
- validate_volume_path(host_path: str, mode: str) -> Tuple[bool, str]
```

#### 3. `validation/docker_validation.py` (~120 lines)
Docker command and parameter validation.

```python
# Contents:
- validate_docker_run_command(command: str) -> Tuple[bool, str]
- validate_docker_params(params: Dict) -> Tuple[bool, str]
```

#### 4. `validation/command_validation.py` (~180 lines)
Command allowlist and validation.

```python
# Contents:
- CommandAllowlistEntry (dataclass)
- COMMAND_ALLOWLIST: List[CommandAllowlistEntry]
- CommandValidator (class)
- validate_command(command: str, timeout: int) -> Tuple[bool, str]
```

#### 5. `validation/__init__.py` (~40 lines)
Public API that maintains backward compatibility.

```python
# Re-exports everything for backward compatibility:
from .constants import (
    BLOCKED_DOCKER_RUN_FLAGS,
    BLOCKED_VOLUME_PATTERNS,
    PROTECTED_PATHS,
    BLOCKED_DOCKER_PARAMS,
)
from .volume_validation import validate_volume_mount
from .docker_validation import (
    validate_docker_run_command,
    validate_docker_params,
)
from .command_validation import (
    CommandAllowlistEntry,
    CommandValidator,
    COMMAND_ALLOWLIST,
    validate_command,
)

__all__ = [...]
```

---

## Dependency Graph

```
                    constants.py
                    /          \
                   /            \
    volume_validation.py    docker_validation.py
                   \            /
                    \          /
               command_validation.py
                        |
                   __init__.py
                        |
              lib/__init__.py (update)
                        |
        ┌───────────────┼───────────────┐
        │               │               │
   security.py    test_security.py  test_validation_extended.py
```

---

## Benefits

### Before (Single File)
- 429 lines in one file
- Mixed responsibilities
- Hard to test in isolation
- Difficult to maintain

### After (Module Package)
| Module | Lines | Responsibility |
|--------|-------|----------------|
| `constants.py` | ~60 | Shared security constants |
| `volume_validation.py` | ~70 | Volume mount checks |
| `docker_validation.py` | ~120 | Docker security |
| `command_validation.py` | ~180 | Command allowlist |
| `__init__.py` | ~40 | Public API |
| **Total** | ~470 | Same functionality, better organization |

### Improvements
1. **Single Responsibility**: Each module has one clear purpose
2. **Testability**: Can test each validator independently
3. **Maintainability**: Easier to find and modify code
4. **Extensibility**: Easy to add new validators
5. **Readability**: Smaller files are easier to understand

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing imports | Maintain backward-compatible `__init__.py` |
| Circular dependencies | Constants module has no internal dependencies |
| Test failures | Update test imports, run full test suite |
| Missing exports | Verify all `__all__` exports match original |

---

## Success Criteria

1. All existing tests pass without modification (except import paths)
2. No changes to public API
3. Each new module is under 200 lines
4. No circular dependencies
5. Code coverage remains at 100% for validation
