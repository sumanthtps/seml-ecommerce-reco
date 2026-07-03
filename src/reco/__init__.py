"""SEML e-commerce recommendation system.

A small but production-shaped reference implementation built for AIMLCZG546
Assignment I. It demonstrates two architectural patterns:

* **API Gateway** - a single authenticated entry point (:func:`reco.gateway`).
* **Event-Driven Architecture** - activity events are queued and processed by a
  background consumer (:func:`reco.recommendation`).

The machine-learning core (item-based collaborative filtering) lives in
:mod:`reco.domain` and is fully decoupled from the web/service layer.
"""

from __future__ import annotations

__version__ = "1.0.0"

__all__ = ["__version__"]
