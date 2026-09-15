#!/usr/bin/env python3
"""Scan Git history, tracked working files, and the built application image."""

import os
import shutil
import subprocess
import tempfile

from common import ROOT, configuration, env_file


def run(args):
    subprocess.run(args, cwd=ROOT, check=True)


if __name__ == "__main__":
    images = env_file(ROOT / "images.lock.env")
    env = configuration()

    gitleaks = images["GITLEAKS_IMAGE"]
    trivy = images["TRIVY_IMAGE"]
    gitleaks_config = ROOT / ".gitleaks.toml"

    if not gitleaks_config.is_file():
        raise SystemExit("Missing .gitleaks.toml")

    print("==> Scanning Git history with Gitleaks")
    run([
        "docker", "run", "--rm",
        "-v", f"{ROOT}:/repo:ro,z",
        "-v", f"{gitleaks_config}:/gitleaks.toml:ro,z",
        gitleaks,
        "git",
        "--config", "/gitleaks.toml",
        "--redact",
        "/repo",
    ])

    print("==> Staging tracked working files for Gitleaks")
    with tempfile.TemporaryDirectory(prefix="liberty-scan-") as directory:
        # Make the temporary tree traversable by containerized scanners.
        os.chmod(directory, 0o755)

        stage = os.path.join(directory, "source")
        os.mkdir(stage, 0o755)

        files = (
            subprocess.check_output(
                ["git", "ls-files", "-z"],
                cwd=ROOT,
            )
            .decode()
            .split("\0")
        )

        copied_files = 0
        copied_bytes = 0

        for name in filter(None, files):
            source = ROOT / name

            if source.is_symlink() or not source.is_file():
                continue

            target = os.path.join(stage, name)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(source, target)

            copied_files += 1
            copied_bytes += source.stat().st_size

        if copied_files == 0 or copied_bytes == 0:
            raise SystemExit(
                "Tracked-source security scan would be empty; refusing to continue."
            )

        print(
            f"Tracked-source scan input: "
            f"{copied_files} files, {copied_bytes} bytes"
        )

        print("==> Scanning tracked working files with Gitleaks")
        run([
            "docker", "run", "--rm",
            "-v", f"{stage}:/source:ro,z",
            "-v", f"{gitleaks_config}:/gitleaks.toml:ro,z",
            gitleaks,
            "dir",
            "--config", "/gitleaks.toml",
            "--redact",
            "/source",
        ])

        print("==> Exporting application image for Trivy")
        image_tar = os.path.join(directory, "image.tar")

        # Stream Docker's output into a file opened by this process. This avoids
        # docker image save --output creating a temporary file under /tmp.
        with open(image_tar, "wb") as image_file:
            subprocess.run(
                ["docker", "image", "save", env["APP_IMAGE"]],
                cwd=ROOT,
                check=True,
                stdout=image_file,
            )

        if os.path.getsize(image_tar) == 0:
            raise SystemExit("Application image export produced an empty archive.")

        print("==> Scanning application image with Trivy")
        run([
            "docker", "run", "--rm",
            "-v", f"{image_tar}:/scan/image.tar:ro,z",
            trivy,
            "image",
            "--input", "/scan/image.tar",
            "--scanners", "vuln",
            "--severity", "HIGH,CRITICAL",
            "--exit-code", "1",
        ])

    print("Secret and high/critical image vulnerability gates passed.")
