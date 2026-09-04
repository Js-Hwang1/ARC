# Kaggle Offline Packaging and Container Strategy

Status: active deployment decision

Date: 2026-09-04

## Short answer

Use Docker on the RTX cluster to build and test the submission environment. Do
not attempt to pull or run that Docker image inside Kaggle.

Kaggle already executes notebooks inside a Kaggle-managed container. Kaggle
Staff states that Docker is not supported inside notebooks, and the competition
requires internet access to be disabled. Therefore a scored notebook has neither
a supported nested Docker daemon nor network access to a container registry.

The deployable unit is:

```text
Kaggle-managed GPU image
        +
pinned, checksum-verified offline wheelhouse/input overlay
        +
pinned model input
        +
thin notebook
```

Our cluster Docker image is the reproducible factory and test environment for
that deployable unit, not the unit Kaggle executes.

## What is allowed and practical

- Build and run our own Docker image on the cluster with NVIDIA Container
  Toolkit and `--gpus`.
- Base the development image on the exact Kaggle GPU image/digest associated
  with a saved notebook version when that image is available.
- Select the saved notebook's original Kaggle environment rather than silently
  moving to the latest image.
- Attach version-pinned Kaggle Datasets, Models, Notebooks, or Packages before
  saving the notebook.
- Attach public model files, Python wheels, native shared libraries, Rust
  wheels/binaries, schemas, and manifests as notebook inputs when their licenses
  and competition rules permit it.
- Use Kaggle's Dependency Manager, which prepares an attached offline dependency
  installation notebook.
- Run `pip` with `--no-index` against an attached wheel directory.
- Launch SGLang/vLLM and our Rust-backed Python package as subprocesses/extensions
  inside the existing Kaggle container.
- Use shell commands that operate only on attached inputs and
  `/kaggle/working`.

The ARC-AGI-3 code requirements allow freely and publicly available external
data, including pretrained models. Prize publication requirements still apply
to our source, build recipe, and artifacts.

## What is unavailable or unsafe to depend on

- `docker pull`, `podman pull`, or any registry access during a scored run;
- starting a Docker daemon or relying on privileged/nested containers;
- uploading a Docker tarball and assuming Kaggle can execute it with GPU access;
- choosing an arbitrary personal Docker image as the competition runtime;
- runtime `apt`, Git, Curl, Hugging Face Hub, or other internet downloads;
- compiling the Rust toolchain or the full CUDA inference stack during scoring;
- changing or bundling the host NVIDIA kernel driver;
- resolving unpinned packages from whatever happens to be preinstalled;
- depending on an attached private artifact when the public milestone notebook
  must be reproducible by competitors and organizers.

Kaggle's "original environment" option pins a Kaggle-provided notebook image. It
does not mean that we can upload and select an arbitrary Dockerfile.

## Reproducibility model

A Docker image cannot freeze the complete scored machine. The host GPU, NVIDIA
driver, competition gateway, and Kaggle orchestration remain outside the
container. Record two contracts:

### Kaggle base contract

- Kaggle image name and immutable digest;
- Python, glibc, CUDA runtime, PyTorch, Triton, and relevant system libraries;
- GPU model/compute capability, NVIDIA driver, host RAM, and vCPU count;
- competition ARC wheel versions.

### Submission overlay contract

- exact SGLang and vLLM wheels used for the comparison;
- exact FlashInfer/attention-kernel wheels;
- all transitive Python wheels not supplied by the base contract;
- our `arc_agent` Python package and `arc-core` PyO3 wheel;
- model, tokenizer, configuration, and chat-template files;
- JSON schemas and configuration;
- SHA-256 digest and size for every artifact.

The notebook verifies both contracts before loading the model.

## Build pipeline

```text
1. Save a minimal Kaggle RTX notebook version.
2. Record its Kaggle environment image/digest and runtime fingerprint.
3. Pull that image on an RTX PRO 6000 cluster node.
4. Build the dependency overlay inside that image.
5. Run unit tests and SGLang/vLLM smoke tests with networking disabled.
6. Produce wheelhouse + lock manifest + source/build metadata.
7. Upload and version the artifact as a Kaggle Dataset/Package input.
8. Attach and pin that exact version to the submission notebook.
9. Save & Run with internet disabled, then compare its fingerprint.
```

Use one full RTX PRO 6000 for parity. Extra cluster GPUs run independent build,
backend, configuration, and regression jobs rather than making one test depend
on hardware unavailable to Kaggle.

## Cluster container

The cluster `Dockerfile` should eventually have this logical structure:

```dockerfile
FROM <exact-kaggle-gpu-image>@sha256:<digest>

# Copy only pinned source/lock metadata.
COPY packaging/ /opt/arc/packaging/
COPY python/ /opt/arc/python/
COPY rust/ /opt/arc/rust/

# Build/download the overlay while cluster networking is available.
# Every resolved artifact is copied into /opt/arc/dist/wheelhouse.

# Run compile/import/smoke tests during image build or CI.
```

Do not write the final Dockerfile until the cluster and first Kaggle RTX runtime
fingerprints are available. Guessing the CUDA/PyTorch/FlashInfer combination is
exactly what containerization is supposed to prevent.

## Wheelhouse artifact

The upload should resemble:

```text
arc-runtime-overlay/
  manifest.json
  requirements-overlay.lock
  constraints-base.txt
  wheels/
    sglang-<pinned>.whl
    vllm-<pinned>.whl
    flashinfer_python-<pinned>.whl
    arc_agent-<commit>.whl
    arc_core-<commit>-cp312-...-x86_64.whl
    ...all required overlay wheels...
  licenses/
  build/
    Dockerfile
    base-image-digest.txt
    build-command.txt
    pip-freeze.txt
    runtime-fingerprint.json
```

`manifest.json` records the relative path, byte size, SHA-256, package/version,
source URL/revision, license, and build platform for each file.

## Notebook installation

The notebook must resolve exactly one pinned input directory, validate its
manifest, and install without an index:

```python
subprocess.check_call([
    sys.executable,
    "-m",
    "pip",
    "install",
    "--no-index",
    "--find-links",
    str(overlay_dir / "wheels"),
    "--constraint",
    str(overlay_dir / "constraints-base.txt"),
    "--requirement",
    str(overlay_dir / "requirements-overlay.lock"),
])
```

The lock must refer only to local artifacts and include hashes. After
installation, import the native modules, compare actual versions to the
manifest, and run a tiny CUDA operation before loading the full model.

Do not blindly reinstall the entire Kaggle environment. Initially treat
Kaggle's CUDA/PyTorch stack as the pinned base and install the smallest tested
overlay. If SGLang requires a conflicting PyTorch build, package a separately
tested isolated Python environment as a deliberate alternative rather than
mutating dependencies ad hoc in notebook cells.

## Dependency Manager vs our wheelhouse

Kaggle's Dependency Manager is allowed and convenient for ordinary Python-only
packages. It prepares wheels in advance so they can be installed with notebook
internet disabled.

Use our explicit wheelhouse for the inference stack because:

- Blackwell CUDA/PyTorch/FlashInfer compatibility is sensitive;
- we need the same artifact on the cluster and Kaggle;
- the Rust extension is custom;
- manifests and hashes make failures auditable;
- we need a reliable vLLM fallback alongside SGLang;
- a public Dataset version is easier to pin and inspect.

Dependency Manager remains acceptable for noncritical utilities, but minimizing
installation mechanisms makes the submission easier to reproduce.

## Offline acceptance test

Before uploading an overlay, start a fresh cluster container with networking
disabled and no user cache mounted. It must:

1. install only from the staged wheelhouse;
2. import PyTorch, SGLang, vLLM, FlashInfer, and the Rust extension;
3. report the expected GPU and compute capability;
4. launch each inference backend separately;
5. load the exact Qwen model from a read-only local mount;
6. return a valid typed decision for a fixed request;
7. pass a short concurrent request test;
8. terminate without orphaned GPU processes.

Only the backend selected for production needs to be shipped in the final
minimal overlay. Keep the dual-backend overlay for development and comparison.

## Sources

- [Kaggle notebook environments and offline Dependency Manager](https://www.kaggle.com/docs/notebooks)
- [Kaggle Staff: Docker is not supported inside notebooks](https://www.kaggle.com/discussions/product-feedback/522012)
- [Kaggle Packages and pinned data sources](https://www.kaggle.com/docs/packages)
- [Kaggle's published Python image](https://github.com/Kaggle/docker-python)
- [ARC-AGI-3 code requirements](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview)
