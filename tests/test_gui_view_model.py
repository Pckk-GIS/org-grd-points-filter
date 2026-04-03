import pytest

from point_filter.gui.view_model import build_app_config, default_state
from point_filter.validation import ConfigurationError


def test_default_state_builds_app_config():
    state = default_state()
    config = build_app_config(state)

    assert str(config.primary_region_input.path).endswith(
        "data\\sample_region\\regions.csv"
    ) or str(config.primary_region_input.path).endswith(
        "data/sample_region/regions.csv"
    )
    assert len(config.region_inputs) == 1
    assert config.primary_region_input.layer is None
    assert config.org_x_col == 2
    assert config.org_y_col == 3
    assert config.org_z_col == 4
    assert config.grd_x_col == 2
    assert config.grd_y_col == 3
    assert config.grd_z_col == 4


def test_build_app_config_rejects_invalid_column():
    state = default_state()
    state.org_x_col = "0"

    with pytest.raises(ConfigurationError):
        build_app_config(state)
