"""Check that the script runs next to a Dapr sidecar."""

import os


def require_sidecar() -> None:
    """Exit with a hint when the script was not started with `dapr run`.

    Without a sidecar the workflow runtime keeps retrying the connection
    and the script appears to hang.
    """
    if not os.getenv("DAPR_GRPC_PORT"):
        raise SystemExit(
            "No Dapr sidecar found. Start this script with "
            "`dapr run --resources-path ./resources -- uv run python <script>.py`."
        )
