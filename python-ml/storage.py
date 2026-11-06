import io
import json
import os

import joblib
from minio import Minio
from minio.error import S3Error

BUCKET = os.environ.get("MINIO_BUCKET", "fraud-detection")
ACTIVE_KEY = "models/active/model.pkl"
VERSIONS_KEY = "models/versions.json"


def get_client() -> Minio:
    host = os.environ.get("MINIO_HOST", "localhost")
    port = os.environ.get("MINIO_PORT", "9000")
    return Minio(
        f"{host}:{port}",
        access_key=os.environ.get("MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.environ.get("MINIO_ROOT_PASSWORD", "minioadmin"),
        secure=False,
    )


def _archive_key(version: str) -> str:
    return f"models/archive/model_{version}.pkl"


def _put(client: Minio, bucket: str, key: str, data: bytes, metadata: dict | None = None) -> None:
    client.put_object(bucket, key, io.BytesIO(data), len(data), metadata=metadata)


def _get(client: Minio, bucket: str, key: str) -> bytes:
    resp = client.get_object(bucket, key)
    try:
        return resp.read()
    finally:
        resp.close()
        resp.release_conn()


def save_model(model, version: str, client: Minio, bucket: str = BUCKET) -> None:
    """Upload a trained model to the archive. It does not go live until activate_model()."""
    buf = io.BytesIO()
    joblib.dump(model, buf)
    _put(client, bucket, _archive_key(version), buf.getvalue())


def activate_model(version: str, client: Minio, bucket: str = BUCKET) -> None:
    """Copy an archived version to models/active/. The active object remembers its version."""
    data = _get(client, bucket, _archive_key(version))
    _put(client, bucket, ACTIVE_KEY, data, metadata={"version": version})


def load_active_model(client: Minio, bucket: str = BUCKET):
    """Return (model, version) for whatever is currently in models/active/."""
    version = client.stat_object(bucket, ACTIVE_KEY).metadata.get("x-amz-meta-version", "unknown")
    return joblib.load(io.BytesIO(_get(client, bucket, ACTIVE_KEY))), version


def load_versions(client: Minio, bucket: str = BUCKET) -> list[dict]:
    """The versions manifest, or an empty list if none has been written yet."""
    try:
        return json.loads(_get(client, bucket, VERSIONS_KEY))["versions"]
    except S3Error as e:
        if e.code == "NoSuchKey":
            return []
        raise


def save_versions(versions: list[dict], client: Minio, bucket: str = BUCKET) -> None:
    _put(client, bucket, VERSIONS_KEY, json.dumps({"versions": versions}, indent=2).encode())


def next_version(client: Minio, bucket: str = BUCKET) -> str:
    return f"v{len(load_versions(client, bucket)) + 1}"


if __name__ == "__main__":
    # Self-check against a live MinIO, in a throwaway bucket so real data is never touched.
    import numpy as np
    from sklearn.ensemble import IsolationForest

    client, bucket = get_client(), "storage-selftest"
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    X = np.random.default_rng(0).normal(size=(500, 3))
    model = IsolationForest(n_estimators=10, random_state=0).fit(X)

    assert load_versions(client, bucket) == []
    assert next_version(client, bucket) == "v1"

    save_model(model, "v1", client, bucket)
    activate_model("v1", client, bucket)
    loaded, version = load_active_model(client, bucket)
    assert version == "v1"
    assert (loaded.predict(X) == model.predict(X)).all()

    save_versions([{"version": "v1", "status": "active"}], client, bucket)
    assert load_versions(client, bucket)[0]["version"] == "v1"
    assert next_version(client, bucket) == "v2"

    for obj in client.list_objects(bucket, recursive=True):
        client.remove_object(bucket, obj.object_name)
    client.remove_bucket(bucket)
    print("storage.py self-check passed")
