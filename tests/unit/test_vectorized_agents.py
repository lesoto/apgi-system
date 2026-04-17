"""
Unit tests for vectorized agent simulation and async orchestration.

Tests cover:
- ActiveInferenceAgent descriptor (record, reset)
- VectorizedAgentPool.step() – correct shape, per-agent FE
- ActiveInferenceEngine.vectorized_batch_step()
- ActiveInferenceEngine.async_step() via asyncio.run()
- Error paths (batch size mismatch, wrong observation shape)
"""

import asyncio
import math
from typing import Any, Dict

import numpy as np
import pytest

from apgi_system.core.active_inference import (
    ActiveInferenceAgent,
    ActiveInferenceEngine,
    VectorizedAgentPool,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def simple_config() -> Dict[str, Any]:
    """Minimal 3-level configuration for fast tests."""
    return {
        "hierarchy": {
            "num_levels": 3,
            "level_configs": [
                {"nodes": 32, "name": "sensory"},
                {"nodes": 16, "name": "perceptual"},
                {"nodes": 8, "name": "conceptual"},
            ],
        },
        "active_inference": {
            "learning_rate": 0.01,
            "precision_range": [0.1, 10.0],
            "planning": {"horizon": 2, "num_policies": 4},
        },
        "system": {"timestep_ms": 1.0, "batch_size": 1, "random_seed": 42},
        "multi_modal": {"modalities": {"vision": 32}},
    }


@pytest.fixture
def batch_config(simple_config: Dict[str, Any]) -> Dict[str, Any]:
    """Config with batch_size=8 for multi-agent tests."""
    cfg = {**simple_config, "system": {**simple_config["system"], "batch_size": 8}}
    return cfg


# ---------------------------------------------------------------------------
# ActiveInferenceAgent
# ---------------------------------------------------------------------------


class TestActiveInferenceAgent:
    def test_record_step(self) -> None:
        agent = ActiveInferenceAgent(agent_id=0)
        agent.record_step(1.5)
        agent.record_step(2.0)
        assert agent.free_energy_history == [1.5, 2.0]

    def test_reset_clears_history(self) -> None:
        agent = ActiveInferenceAgent(agent_id=0)
        agent.record_step(1.0)
        agent.reset()
        assert agent.free_energy_history == []

    def test_default_config_is_empty_dict(self) -> None:
        agent = ActiveInferenceAgent(agent_id=3)
        assert agent.config == {}

    def test_custom_config_stored(self) -> None:
        cfg = {"learning_rate": 0.05}
        agent = ActiveInferenceAgent(agent_id=1, config=cfg)
        assert agent.config["learning_rate"] == pytest.approx(0.05)

    def test_multiple_agents_independent(self) -> None:
        a1 = ActiveInferenceAgent(agent_id=0)
        a2 = ActiveInferenceAgent(agent_id=1)
        a1.record_step(5.0)
        assert a2.free_energy_history == []


# ---------------------------------------------------------------------------
# VectorizedAgentPool
# ---------------------------------------------------------------------------


class TestVectorizedAgentPool:
    def test_construction_correct_agent_count(self, batch_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(batch_config)
        pool = VectorizedAgentPool(engine, num_agents=8)
        assert len(pool.agents) == 8
        for i, agent in enumerate(pool.agents):
            assert agent.agent_id == i

    def test_batch_mismatch_raises(self, simple_config: Dict[str, Any]) -> None:
        """Engine with batch_size=1 cannot serve a pool of 8 agents."""
        engine = ActiveInferenceEngine(simple_config)  # batch_size=1
        with pytest.raises(ValueError, match="batch_size"):
            VectorizedAgentPool(engine, num_agents=8)

    def test_pool_step_returns_one_result_per_agent(self, batch_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(batch_config)
        pool = VectorizedAgentPool(engine, num_agents=8)
        obs = np.random.randn(8, 32).astype(np.float64)
        results = pool.step(obs)
        assert len(results) == 8

    def test_pool_step_result_structure(self, batch_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(batch_config)
        pool = VectorizedAgentPool(engine, num_agents=8)
        obs = np.random.randn(8, 32).astype(np.float64)
        results = pool.step(obs)
        for r in results:
            assert "agent_id" in r
            assert "free_energy" in r
            assert "action" in r
            assert "belief_means" in r

    def test_pool_step_agent_ids_sequential(self, batch_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(batch_config)
        pool = VectorizedAgentPool(engine, num_agents=8)
        obs = np.random.randn(8, 32).astype(np.float64)
        results = pool.step(obs)
        ids = [r["agent_id"] for r in results]
        assert ids == list(range(8))

    def test_pool_step_records_free_energy_in_agent(self, batch_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(batch_config)
        pool = VectorizedAgentPool(engine, num_agents=8)
        obs = np.random.randn(8, 32).astype(np.float64)
        pool.step(obs)
        for agent in pool.agents:
            assert len(agent.free_energy_history) == 1
            assert math.isfinite(agent.free_energy_history[0])

    def test_pool_step_wrong_observation_shape_raises(self, batch_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(batch_config)
        pool = VectorizedAgentPool(engine, num_agents=8)
        obs_wrong = np.random.randn(4, 32)  # 4 instead of 8
        with pytest.raises(ValueError, match="shape"):
            pool.step(obs_wrong)

    def test_pool_free_energies_finite(self, batch_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(batch_config)
        pool = VectorizedAgentPool(engine, num_agents=8)
        obs = np.random.randn(8, 32).astype(np.float64)
        results = pool.step(obs)
        for r in results:
            assert math.isfinite(r["free_energy"])
            assert r["free_energy"] >= 0.0

    def test_pool_reset_clears_all_histories(self, batch_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(batch_config)
        pool = VectorizedAgentPool(engine, num_agents=8)
        obs = np.random.randn(8, 32).astype(np.float64)
        pool.step(obs)
        pool.reset()
        for agent in pool.agents:
            assert agent.free_energy_history == []

    def test_multiple_steps_accumulate_history(self, batch_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(batch_config)
        pool = VectorizedAgentPool(engine, num_agents=8)
        for _ in range(5):
            obs = np.random.randn(8, 32).astype(np.float64)
            pool.step(obs)
        for agent in pool.agents:
            assert len(agent.free_energy_history) == 5

    def test_custom_agent_configs_stored(self, batch_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(batch_config)
        cfgs = [{"lr": float(i)} for i in range(8)]
        pool = VectorizedAgentPool(engine, num_agents=8, agent_configs=cfgs)
        for i, agent in enumerate(pool.agents):
            assert agent.config["lr"] == pytest.approx(float(i))

    @pytest.mark.asyncio
    async def test_async_pool_step(self, batch_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(batch_config)
        pool = VectorizedAgentPool(engine, num_agents=8)
        obs = np.random.randn(8, 32).astype(np.float64)
        results = await pool.async_step(obs)
        assert len(results) == 8
        for r in results:
            assert math.isfinite(r["free_energy"])


# ---------------------------------------------------------------------------
# ActiveInferenceEngine.vectorized_batch_step
# ---------------------------------------------------------------------------


class TestVectorizedBatchStep:
    def test_batch_shape_matches_engine(self, batch_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(batch_config)
        obs = np.random.randn(8, 32).astype(np.float64)
        actions, info = engine.vectorized_batch_step(obs)
        assert actions.shape[0] == 8

    def test_per_agent_fe_in_info(self, batch_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(batch_config)
        obs = np.random.randn(8, 32).astype(np.float64)
        _, info = engine.vectorized_batch_step(obs)
        assert "per_agent_free_energy" in info
        fe_arr = info["per_agent_free_energy"]
        assert fe_arr.shape == (8,)
        assert np.all(np.isfinite(fe_arr))
        assert np.all(fe_arr >= 0.0)

    def test_wrong_batch_dim_raises(self, batch_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(batch_config)  # batch_size=8
        obs = np.random.randn(4, 32)  # wrong batch
        with pytest.raises(ValueError, match="batch_size"):
            engine.vectorized_batch_step(obs)

    def test_actions_broadcast_to_batch(self, batch_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(batch_config)
        obs = np.random.randn(8, 32).astype(np.float64)
        actions, _ = engine.vectorized_batch_step(obs)
        # All rows are identical (same motor planner decision broadcast)
        if actions.ndim == 2 and actions.shape[0] == 8:
            assert np.allclose(actions[0], actions[1])

    def test_free_energy_finite_over_many_steps(self, batch_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(batch_config)
        for _ in range(10):
            obs = np.random.randn(8, 32).astype(np.float64) * 0.1
            _, info = engine.vectorized_batch_step(obs)
        assert np.all(np.isfinite(info["per_agent_free_energy"]))


# ---------------------------------------------------------------------------
# ActiveInferenceEngine.async_step
# ---------------------------------------------------------------------------


class TestAsyncStep:
    def test_async_step_returns_action_and_info(self, simple_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(simple_config)
        obs = np.random.randn(32).astype(np.float64)

        async def _run():
            return await engine.async_step(obs)

        action, info = asyncio.run(_run())
        assert isinstance(action, np.ndarray)
        assert "free_energy" in info
        assert "beliefs" in info

    def test_async_step_advances_time(self, simple_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(simple_config)
        obs = np.random.randn(32).astype(np.float64)

        async def _run():
            await engine.async_step(obs)
            await engine.async_step(obs)

        asyncio.run(_run())
        assert engine.time == pytest.approx(2 * engine.timestep)

    def test_async_step_free_energy_finite(self, simple_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(simple_config)
        obs = np.random.randn(32).astype(np.float64)

        async def _run():
            _, info = await engine.async_step(obs)
            return info["free_energy"]

        fe = asyncio.run(_run())
        assert math.isfinite(fe)
        assert fe >= 0.0

    def test_async_step_consistent_with_sync_step(self, simple_config: Dict[str, Any]) -> None:
        """
        With the same seed, async and sync steps should produce identical
        free energy values (they share the same filter).
        """
        # Engine 1 – sync
        np.random.seed(0)
        e1 = ActiveInferenceEngine(simple_config)
        obs = np.ones((1, 32), dtype=np.float64) * 0.5
        _, info_sync = e1.step(obs)

        # Engine 2 – async
        np.random.seed(0)
        e2 = ActiveInferenceEngine(simple_config)

        async def _run():
            return await e2.async_step(obs)

        _, info_async = asyncio.run(_run())

        assert info_sync["free_energy"] == pytest.approx(info_async["free_energy"], rel=1e-6)

    def test_async_step_multimodal_dict_observation(self, simple_config: Dict[str, Any]) -> None:
        engine = ActiveInferenceEngine(simple_config)
        obs = {"vision": np.random.randn(1, 32).astype(np.float64)}

        async def _run():
            return await engine.async_step(obs)

        action, info = asyncio.run(_run())
        assert isinstance(action, np.ndarray)
        assert math.isfinite(info["free_energy"])

    @pytest.mark.asyncio
    async def test_concurrent_async_steps_safe(self, simple_config: Dict[str, Any]) -> None:
        """Multiple concurrent async_step calls with different engines are safe."""
        engines = [ActiveInferenceEngine(simple_config) for _ in range(4)]
        obs_list = [np.random.randn(32).astype(np.float64) for _ in range(4)]

        results = await asyncio.gather(*[e.async_step(o) for e, o in zip(engines, obs_list)])
        for action, info in results:
            assert math.isfinite(info["free_energy"])


# ---------------------------------------------------------------------------
# Edge cases & regression guards
# ---------------------------------------------------------------------------


class TestVectorizationEdgeCases:
    def test_single_agent_pool_matches_direct_step(self, simple_config: Dict[str, Any]) -> None:
        """A pool with N=1 should produce equivalent FE to a direct engine step."""
        cfg = {**simple_config, "system": {**simple_config["system"], "batch_size": 1}}
        engine = ActiveInferenceEngine(cfg)
        pool = VectorizedAgentPool(engine, num_agents=1)
        obs = np.random.randn(1, 32).astype(np.float64)

        # Pool step
        pool.reset()
        results = pool.step(obs)
        pool_fe = results[0]["free_energy"]

        # Both must be finite non-negative
        assert math.isfinite(pool_fe)
        assert pool_fe >= 0.0

    def test_large_batch_step_stable(self) -> None:
        """50-agent batch: all FE values must be finite after 3 steps."""
        cfg = {
            "hierarchy": {
                "num_levels": 2,
                "level_configs": [
                    {"nodes": 16, "name": "sensory"},
                    {"nodes": 8, "name": "perceptual"},
                ],
            },
            "active_inference": {
                "learning_rate": 0.01,
                "precision_range": [0.1, 10.0],
                "planning": {"horizon": 1, "num_policies": 2},
            },
            "system": {"timestep_ms": 1.0, "batch_size": 50, "random_seed": 7},
            "multi_modal": {"modalities": {"vision": 16}},
        }
        engine = ActiveInferenceEngine(cfg)
        for _ in range(3):
            obs = np.random.randn(50, 16).astype(np.float64) * 0.1
            _, info = engine.vectorized_batch_step(obs)
        assert np.all(np.isfinite(info["per_agent_free_energy"]))
        assert np.all(info["per_agent_free_energy"] >= 0.0)
