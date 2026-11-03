"""The API on mocked models, for the Playwright smoke test (frontend/e2e/): real worker and DB."""

import tempfile
from pathlib import Path

from tests.test_api import Rig

app = Rig(Path(tempfile.mkdtemp())).app
