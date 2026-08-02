# Authoritative Engineering Blueprint & Precise Implementation Guide

## Systems Architecture Recommendation

* **Target System**: Performance, utility-first AI chat agent for real-world kitchen planning.
* **Core Requirements**: Extreme Token Efficiency (~50% fewer steps, ~4× fewer output tokens on high-volume loops) + Commoditized Intelligence Pricing (flash/mid-tier effective cost for near-Opus capability on background loops).
* **Primary Stack Preference**: C++ for the agent runtime.
* **User Flow Priority**: Accurate floorplan/layout → 2D/3D space reconstruction with 98% accuracy is the non-negotiable foundation.

## CRITICAL RULES (non-negotiable):
* Do not preserve backward compatibility.
* Choose the simplest implementation that fully meets the current requirements.
* Prefer established, well-maintained libraries over custom implementation.
* Llama.cpp C++ primary agent runtime.
* Open WebUI SvelteKit Frontend.
* Raster2Seq floorplan reconstruction engine (https://github.com).
* Single-process C++ agent loop for Extreme Token Efficiency.
* Autonomous loops must never touch the user-facing chat interface portal.

## Routing Rule (Efficiency Core):
* **Floorplan reconstruction path** → Raster2Seq specialist pipeline (deterministic + VLM assist for input normalization).
* **Interactive chat, planning, refinement, storage reasoning** → Grok-4.5.
* **One-shot kitchen synthesis / high-fidelity generation** → Cosmos 3 (prefer Cosmos Nano or Cosmos 4-Step distilled).
* **High-volume autonomous loops** stay inside the C++ runtime and never touch the portal.
                                            
