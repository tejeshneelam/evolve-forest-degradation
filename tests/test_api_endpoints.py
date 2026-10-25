"""
EvOLve Test Suite — tests/test_api_endpoints.py
Functional validation of core FastAPI REST API routes.
"""

def test_api_summary(client):
    """Verifies platform summary statistics endpoint."""
    res = client.get("/api/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_patches" in data
    assert "total_carbon_tco2" in data or "total_carbon_tCO2" in data or "healthy_patches" in data


def test_api_patches(client):
    """Verifies patches geojson/array endpoint."""
    res = client.get("/api/patches")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, (list, dict))
    if isinstance(data, list):
        assert len(data) > 0
        p0 = data[0]
        assert "patch_id" in p0


def test_api_corridors(client):
    """Verifies wildlife migration corridor analysis."""
    res = client.get("/api/corridors")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, (list, dict))


def test_api_fire_risk(client):
    """Verifies fire risk and fuel load monitoring."""
    res = client.get("/api/fire-risk")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, (list, dict))


def test_api_landslide(client):
    """Verifies landslide vulnerability evaluation."""
    res = client.get("/api/landslide")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, (list, dict))


def test_api_carbon(client):
    """Verifies carbon biomass quantification."""
    res = client.get("/api/carbon")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, (list, dict))


def test_api_spectral_bands_meta(client):
    """Verifies Sentinel-2 12-band spectral metadata endpoint."""
    res = client.get("/api/spectral-bands-meta")
    assert res.status_code == 200
    data = res.json()
    assert "bands" in data
    assert len(data["bands"]) == 12
    band_ids = [b["id"] for b in data["bands"]]
    assert "B8" in band_ids
    assert "B11" in band_ids
    assert "NDVI" in band_ids


def test_api_feature_selection_results(client):
    """Verifies GA band selection results endpoint."""
    res = client.get("/api/feature-selection-results")
    assert res.status_code == 200
    data = res.json()
    assert "best_solution" in data
    assert "selected_bands" in data["best_solution"]
    assert len(data["best_solution"]["selected_bands"]) > 0
    assert "pareto_frontier" in data


def test_api_history_vault(client):
    """Verifies SQLite history ledger endpoints."""
    res = client.get("/api/history/queries")
    assert res.status_code == 200
    data = res.json()
    assert "queries" in data

    res_stats = client.get("/api/history/stats")
    assert res_stats.status_code == 200
    data_stats = res_stats.json()
    assert "stats" in data_stats
    assert "total_queries" in data_stats["stats"]

