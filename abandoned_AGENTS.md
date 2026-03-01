# Source of Truth
When instructed to generate or modify a file:

Locate its specification at specs/<name>.spec/

# spec structure
public.md — Defines the public API. This is the authoritative contract.

impl.md — Optional implementation guidance and internal constraints.
# Generating a File From a Spec
When generating a file from a specification:
1) Parse public.md first
2) Extract all public types, functions, classes, constants, and behaviors.
3) Treat this as a strict contract.
4) Then parse impl.md (if present) Use it only for internal structure, algorithm hints, or constraints.
Do not expose anything from impl.md unless it appears in public.md.

The generated file must:
- Fully implement everything defined in public.md.
- Not expose additional public surface area.
- Not contradict the spec.

## Dependency
If a spec says it can rely on another file in the program first check for the public.md for the spec of that file and then check for the source code if that does not exist
## Update
If told to update a file check the spec and see if the spec is not being met in some way.
## Reroll
if told to reroll a file delete the original source code file without reading it and regenerate from the spec.
