#!/usr/bin/env python3
"""Scan Git history, tracked working files, and the built application image."""

import os
import shutil
import subprocess
import tempfile

from common import ROOT, configuration, env_file


def run(args):
    """Run a security command and fail cleanly on an error."""
    result = subprocess.run(args, cwd=ROOT)

    if result.returncode == 0:
        return

    command = " ".join(str(arg) for arg in args)

    if (
        len(args) >= 3
        and args[:3] == ["docker", "scout", "cves"]
        and result.returncode == 2
    ):
        raise SystemExit(
            "Security gate failed: Docker Scout detected "
            f"matching vulnerabilities.\nCommand: {command}"
        )

    raise SystemExit(
        f"Command failed with exit code {result.returncode}: {command}"
    )


if __name__ == "__main__":
    images = env_file(ROOT / "images.lock.env")
    env = configuration()

    gitleaks = images["GITLEAKS_IMAGE"]
    trivy = images["TRIVY_IMAGE"]
    app_image = env["APP_IMAGE"]

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
        os.chmod(stage, 0o755)

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
            parent = os.path.dirname(target)

            os.makedirs(parent, exist_ok=True)
            shutil.copyfile(source, target)

            copied_files += 1
            copied_bytes += source.stat().st_size

        if copied_files == 0 or copied_bytes == 0:
            raise SystemExit(
                "Tracked-source security scan would be empty; "
                "refusing to continue."
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

        print(
            "==> Checking application-introduced HIGH/CRITICAL "
            "vulnerabilities with Docker Scout"
        )
        run([
            "docker", "scout", "cves",
            "--ignore-base",
            "--only-severity", "critical,high",
            "--exit-code",
            app_image,
        ])

        print(
            "==> Checking VEX-affected full-image HIGH/CRITICAL "
            "vulnerabilities with Docker Scout"
        )
        run([
            "docker", "scout", "cves",
            "--only-vex-affected",
            "--only-severity", "critical,high",
            "--exit-code",
            app_image,
        ])

        print("==> Exporting application image for advisory Trivy scan")
        image_tar = os.path.join(directory, "image.tar")

        # Stream Docker's output into a file opened by this process.
        # This avoids docker image save --output creating a temporary
        # file under /tmp.
        with open(image_tar, "wb") as image_file:
            subprocess.run(
                ["docker", "image", "save", app_image],
                cwd=ROOT,
                check=True,
                stdout=image_file,
            )

        if not os.path.isfile(image_tar):
            raise SystemExit(
                "Application image export did not create an archive."
            )

        if os.path.getsize(image_tar) == 0:
            raise SystemExit(
                "Application image export produced an empty archive."
            )

        print("==> Running advisory Trivy whole-image scan")
        run([
            "docker", "run", "--rm",
            "-v", f"{image_tar}:/scan/image.tar:ro,z",
            trivy,
            "image",
            "--input", "/scan/image.tar",
            "--scanners", "vuln",
            "--severity", "HIGH,CRITICAL",
            "--exit-code", "0",
        ])

    print(
        "Secret and VEX-aware HIGH/CRITICAL "
        "image vulnerability gates passed."
    )
