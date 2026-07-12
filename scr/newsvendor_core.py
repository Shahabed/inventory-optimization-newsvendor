#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
newsvendor_core.py
==================

Core reusable functions for the Newsvendor (Newsboy) inventory optimization model.

This module contains the production-grade implementation used in the
Marktoptimierung project for calculating optimal order quantities (Q)
that minimize expected overage and underage costs.

The implementation follows the classic critical fractile approach using
the empirical distribution of demand.

Author: S.C. Azizabadi
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Optional, Union


def calculate_critical_ratio(c_u: float, c_o: float) -> float:
    """
    Calculate the critical ratio (optimal cycle service level).

    The critical ratio represents the probability that demand will be
    less than or equal to the optimal order quantity Q*.

    Formula:
        critical_ratio = c_u / (c_u + c_o)

    Parameters
    ----------
    c_u : float
        Underage cost per unit (cost of stocking one unit too few).
    c_o : float
        Overage cost per unit (cost of stocking one unit too many).

    Returns
    -------
    float
        Critical ratio between 0 and 1.

    Raises
    ------
    ValueError
        If c_u <= 0 or c_o < 0.
    """
    if c_u <= 0:
        raise ValueError("Underage cost (c_u) must be strictly positive.")
    if c_o < 0:
        raise ValueError("Overage cost (c_o) cannot be negative.")

    return c_u / (c_u + c_o)


def calc_newsvendor(
    Demand: pd.Series,
    critical: float,
    round_demand: bool = True
) -> int:
    """
    Calculate the optimal order quantity using the empirical Newsvendor model.

    This is the core production function used across single-shop,
    per-wholesaler (Grosso), and full-network calculations in the
    Marktoptimierung project.

    The function computes the smallest Q such that:
        P(Demand <= Q) >= critical_ratio

    Parameters
    ----------
    Demand : pd.Series
        Historical demand observations (can contain floats; will be rounded
        to nearest integer by default).
    critical : float
        Critical ratio (service level), typically between 0.7 and 0.95.
        Can be calculated with `calculate_critical_ratio(c_u, c_o)`.
    round_demand : bool, default True
        Whether to round demand values to integers before computing the
        empirical distribution. Set to False only if demand is already integer.

    Returns
    -------
    int
        Optimal order quantity Q*.

    Notes
    -----
    - Uses the empirical cumulative distribution function (CDF).
    - If no demand value satisfies the critical ratio (very rare), returns
      the maximum observed demand.
    - Designed to work efficiently with pandas GroupBy.apply().
    """
    if Demand is None or len(Demand) == 0:
        return 0

    demand = Demand.copy()

    if round_demand:
        demand = demand.round(0)

    demand = demand.astype(int)

    # Empirical probability mass function
    pmf = demand.value_counts(normalize=True).sort_index()

    # Empirical cumulative distribution function
    cdf = pmf.cumsum()

    # Find the smallest Q where CDF(Q) >= critical
    candidates = cdf[cdf >= critical]

    if len(candidates) == 0:
        # Fallback: return maximum observed demand
        return int(demand.max())

    opt_q = candidates.index.min()
    return int(opt_q)


def newsvendor_optimal_quantity(
    Demand: pd.Series,
    c_u: float,
    c_o: float,
    round_demand: bool = True
) -> int:
    """
    Convenience wrapper that calculates the critical ratio internally
    and returns the optimal Newsvendor quantity.

    Parameters
    ----------
    Demand : pd.Series
        Historical demand observations.
    c_u : float
        Underage cost per unit.
    c_o : float
        Overage cost per unit.
    round_demand : bool, default True
        Whether to round demand to integers.

    Returns
    -------
    int
        Optimal order quantity Q*.
    """
    critical = calculate_critical_ratio(c_u, c_o)
    return calc_newsvendor(Demand, critical, round_demand=round_demand)


def expected_cost(
    Q: int,
    Demand: pd.Series,
    c_u: float,
    c_o: float,
    round_demand: bool = True
) -> float:
    """
    Calculate the expected cost for a given order quantity Q.

    This is useful for sensitivity analysis and comparing different
    ordering policies.

    Parameters
    ----------
    Q : int
        Order quantity to evaluate.
    Demand : pd.Series
        Historical demand observations.
    c_u : float
        Underage cost per unit.
    c_o : float
        Overage cost per unit.
    round_demand : bool, default True
        Whether to round demand to integers.

    Returns
    -------
    float
        Expected cost = c_u * E[max(D - Q, 0)] + c_o * E[max(Q - D, 0)]
    """
    if round_demand:
        d = Demand.round(0).astype(int)
    else:
        d = Demand.astype(int)

    underage = np.maximum(d - Q, 0).mean()
    overage = np.maximum(Q - d, 0).mean()

    return c_u * underage + c_o * overage


# =============================================================================
# Example usage (for documentation / testing)
# =============================================================================
if __name__ == "__main__":
    # Example with synthetic demand data
    np.random.seed(42)
    example_demand = pd.Series(np.random.poisson(lam=45, size=200))

    c_u = 0.35
    c_o = 0.095

    print("Critical ratio:", calculate_critical_ratio(c_u, c_o))
    print("Optimal Q:", newsvendor_optimal_quantity(example_demand, c_u, c_o))
    print("Expected cost at optimal Q:",
          expected_cost(newsvendor_optimal_quantity(example_demand, c_u, c_o),
                        example_demand, c_u, c_o))
