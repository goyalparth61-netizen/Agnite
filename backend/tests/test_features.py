"""
Tests for feature engineering service (base features, recurrence signals, HotspotFeatures assembly).
"""

from app.schemas.analysis import AnalysisContext
from app.schemas.observation import Observation
from app.services.feature_service import build_hotspot_features, extract_base_features
from app.services.history_service import compute_history


def make_obs(id_str: str, lat: float, lon: float, dt_str: str, frp: float, source: str = "firms") -> Observation:
    return Observation(
        id=id_str,
        latitude=lat,
        longitude=lon,
        observedAt=dt_str,
        frp=frp,
        source=source,  # type: ignore[arg-type]
    )


class TestFeatureService:
    def test_correct_base_feature_calculation(self):
        o1 = make_obs("o1", 21.1466, 79.0889, "2026-09-10T12:00:00.000Z", 20.0, "firms")
        o2 = make_obs("o2", 21.1480, 79.0895, "2026-09-11T12:00:00.000Z", 25.0, "firms")
        o3 = make_obs("o3", 21.1466, 79.0889, "2026-09-12T12:00:00.000Z", 30.0, "manual")
        o4 = make_obs("o4", 21.1500, 79.0900, "2026-09-13T12:00:00.000Z", 35.0, "imported")

        obs_list = [o1, o2, o3, o4]
        history = compute_history(obs_list)
        selected = o4
        context = AnalysisContext(
            industrialDistanceKm=1.5,
            landCover="industrial",
            windKph=20.0,
        )

        base = extract_base_features(history, obs_list, selected, context)

        assert base.current_frp == 35.0
        assert base.observation_count == 4
        assert base.unique_days == 4
        assert base.distinct_passes_count == 4
        assert base.firms_count == 2
        assert base.manual_count == 1
        assert base.imported_count == 1
        assert base.industrial_distance_km == 1.5
        assert base.land_cover == "industrial"
        assert base.wind_kph == 20.0
        assert base.spatial_spread_km > 0.0

    def test_missing_optional_context(self):
        o1 = make_obs("o1", 21.1466, 79.0889, "2026-09-13T12:00:00.000Z", 20.0)
        history = compute_history([o1])

        # No context passed
        base = extract_base_features(history, [o1], o1, None)

        assert base.land_cover == "unknown"
        assert base.industrial_distance_km is None
        assert base.wind_kph is None

    def test_consolidated_hotspot_features_with_recurrence(self):
        # 5 passes across 4 days -> High recurrence signal
        o1 = make_obs("o1", 21.1466, 79.0889, "2026-09-10T12:00:00.000Z", 20.0)
        o2 = make_obs("o2", 21.1466, 79.0889, "2026-09-11T12:00:00.000Z", 22.0)
        o3 = make_obs("o3", 21.1466, 79.0889, "2026-09-12T12:00:00.000Z", 21.0)
        o4 = make_obs("o4", 21.1466, 79.0889, "2026-09-13T06:00:00.000Z", 23.0)
        o5 = make_obs("o5", 21.1466, 79.0889, "2026-09-13T12:00:00.000Z", 24.0)

        obs_list = [o1, o2, o3, o4, o5]
        history = compute_history(obs_list)
        features = build_hotspot_features(history, obs_list, o5)

        assert features.recurrence_signal == "HIGH"
        assert features.persistence_score >= 60.0
        assert features.persistence_status in ("HIGH_PERSISTENCE", "MODERATE_PERSISTENCE")

    def test_single_observation_recurrence_signal(self):
        o1 = make_obs("o1", 21.1466, 79.0889, "2026-09-13T12:00:00.000Z", 20.0)
        history = compute_history([o1])
        features = build_hotspot_features(history, [o1], o1)

        assert features.recurrence_signal == "INSUFFICIENT_HISTORY"
        assert features.persistence_status == "INSUFFICIENT_HISTORY"
