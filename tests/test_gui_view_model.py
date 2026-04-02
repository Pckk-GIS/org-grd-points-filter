import pytest

from point_filter.gui.view_model import build_app_config, default_state
from point_filter.validation import ConfigurationError


def test_default_state_builds_app_config():
    config = build_app_config(default_state())

    assert str(config.region_csv).endswith("data\\regions.csv") or str(
        config.region_csv
    ).endswith("data/regions.csv")
    assert config.x_col == 2
    assert config.y_col == 3
    assert config.z_col == 4


def test_build_app_config_rejects_invalid_column():
    state = default_state()
    state.x_col = "0"

    with pytest.raises(ConfigurationError):
        build_app_config(state)
