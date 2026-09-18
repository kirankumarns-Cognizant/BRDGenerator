"""
Repository acquisition for the sidebar: pick an existing repo, upload a .zip, or
fetch a remote repo by URL.

Remote fetch downloads the forge's zip archive rather than shelling out to git.
No pipeline agent reads git metadata, so a working tree without .git is
equivalent — and this keeps the app working on machines with no git installed.
"""

import shutil
import tempfile
import time
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

_SUPPORTED_HOSTS = ("github.com", "gitlab.com", "bitbucket.org")
_MODES = ("Existing repo", "Upload .zip", "Git URL")


def replace_dir(target: Path) -> None:
    """Remove `target` so it can be rewritten, falling back when Windows locks it.

    On Windows a file open in an editor or scanner blocks rmtree, so move the
    directory aside instead; as a last resort leave it and let the copy overwrite.
    """
    if not target.exists():
        return
    try:
        shutil.rmtree(target, ignore_errors=False)
        return
    except (PermissionError, OSError):
        pass
    try:
        aside = Path(tempfile.gettempdir()) / f"{target.name}_old_{int(time.time())}"
        shutil.move(str(target), str(aside))
    except Exception:
        pass


def _payload_root(extracted: Path) -> Path:
    """Return the directory holding the repo itself.

    Archives from GitHub/GitLab and most hand-made zips wrap everything in a
    single top-level folder; unwrap it so the repo doesn't nest one level deep.
    """
    entries = [e for e in extracted.iterdir() if e.name != "__MACOSX"]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return extracted


def unpack_into(archive: Path, dest: Path) -> None:
    """Extract `archive` over `dest`, replacing whatever was there."""
    staging = Path(tempfile.mkdtemp())
    try:
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(staging)
        source = _payload_root(staging)
        replace_dir(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, dest, dirs_exist_ok=True)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def parse_repo_url(url: str, ref: str = "") -> tuple[str, list[str]]:
    """Resolve a repository URL to (repo_name, candidate archive URLs).

    Restricting to known forges keeps this server-side fetch of a user-supplied
    URL bounded without building a full SSRF allowlist.
    """
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("URL must start with https://")

    if parsed.path.lower().endswith(".zip"):
        return Path(parsed.path).stem, [url]

    host = parsed.netloc.lower().removeprefix("www.")
    if host not in _SUPPORTED_HOSTS:
        raise ValueError(
            f"Unsupported host '{host or '?'}'. Use "
            f"{', '.join(_SUPPORTED_HOSTS)}, or a direct .zip URL."
        )

    parts = [s for s in parsed.path.split("/") if s]
    # Trim the trailing /tree/<branch> or /-/tree/<branch> of a browser URL.
    for marker in ("tree", "-", "blob", "src"):
        if marker in parts[2:3]:
            parts = parts[:2]
            break
    if len(parts) < 2:
        raise ValueError("URL must include owner and repository, e.g. https://github.com/owner/repo")

    owner, repo = parts[0], parts[1].removesuffix(".git")
    refs = [ref.strip()] if ref.strip() else ["main", "master"]

    candidates = []
    for r in refs:
        if host == "github.com":
            candidates.append(f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{r}")
        elif host == "gitlab.com":
            candidates.append(f"https://gitlab.com/{owner}/{repo}/-/archive/{r}/{repo}-{r}.zip")
        else:
            candidates.append(f"https://bitbucket.org/{owner}/{repo}/get/{r}.zip")
    return repo, candidates


def _auth_headers(url: str, token: str) -> dict:
    if not token:
        return {}
    if "gitlab.com" in url:
        return {"PRIVATE-TOKEN": token}
    return {"Authorization": f"Bearer {token}"}


def fetch_repo(url: str, ref: str, token: str, project_root: Path) -> tuple[bool, str]:
    """Download a repo archive into Sample_Repos/<name>. Returns (ok, message)."""
    import requests

    # Corporate TLS interception re-signs certificates with an internal CA that
    # certifi doesn't carry, but the OS trust store does. Idempotent.
    try:
        import truststore

        truststore.inject_into_ssl()
    except ImportError:
        pass

    try:
        repo_name, candidates = parse_repo_url(url, ref)
    except ValueError as exc:
        return False, str(exc)

    dest = project_root / "Sample_Repos" / repo_name
    last_error = "no candidate URL succeeded"

    for candidate in candidates:
        try:
            response = requests.get(
                candidate,
                headers=_auth_headers(candidate, token),
                stream=True,
                timeout=120,
                allow_redirects=True,
            )
        except requests.RequestException as exc:
            last_error = f"network error: {exc}"
            continue

        if response.status_code != 200:
            reason = {
                401: "authentication required — provide a token",
                403: "access forbidden — token may lack permission",
                404: "not found — check the URL and branch name",
            }.get(response.status_code, f"HTTP {response.status_code}")
            last_error = reason
            continue

        tmp_dir = Path(tempfile.mkdtemp())
        archive = tmp_dir / "repo.zip"
        try:
            with open(archive, "wb") as fh:
                for chunk in response.iter_content(chunk_size=1 << 16):
                    fh.write(chunk)
            unpack_into(archive, dest)
        except zipfile.BadZipFile:
            last_error = "downloaded file was not a valid zip archive"
            continue
        except Exception as exc:
            return False, f"Could not unpack {repo_name}: {exc}"
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        (project_root / "KB" / repo_name).mkdir(parents=True, exist_ok=True)
        return True, repo_name

    return False, f"Could not fetch repository: {last_error}"


def _render_upload(project_root: Path) -> str | None:
    """Zip upload. Returns the repo name when one was just stored."""
    uploaded = st.file_uploader(
        "Repository .zip",
        type=["zip"],
        help="A zipped source repository to analyse.",
        key="repo_zip_uploader",
    )
    if uploaded is None:
        return None

    tmp_dir = Path(tempfile.mkdtemp())
    archive = tmp_dir / uploaded.name
    try:
        archive.write_bytes(uploaded.getbuffer())
        staging = Path(tempfile.mkdtemp())
        try:
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(staging)
            repo_name = _payload_root(staging).name
        finally:
            shutil.rmtree(staging, ignore_errors=True)

        if repo_name in (".", ""):
            st.error("Could not determine a repository name from that zip.")
            return None

        unpack_into(archive, project_root / "Sample_Repos" / repo_name)
        (project_root / "KB" / repo_name).mkdir(parents=True, exist_ok=True)
    except zipfile.BadZipFile:
        st.error("That file is not a valid zip archive.")
        return None
    except Exception as exc:
        st.error(f"Could not store repository: {exc}")
        return None
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    st.caption(f"Stored in `Sample_Repos/{repo_name}`")
    return repo_name


def _render_git_url(project_root: Path) -> str | None:
    """Remote fetch by URL. Returns the repo name when one was just stored."""
    url = st.text_input(
        "Repository URL",
        key="repo_git_url",
        placeholder="https://github.com/owner/repo",
        help="GitHub, GitLab or Bitbucket. A direct .zip URL also works.",
    )
    ref = st.text_input(
        "Branch or tag",
        key="repo_git_ref",
        placeholder="main",
        help="Leave blank to try main, then master.",
    )
    token = st.text_input(
        "Access token",
        key="repo_git_token",
        type="password",
        help="Only needed for private repositories.",
    )

    existing = (project_root / "Sample_Repos" / Path(urlparse(url.strip()).path).name.removesuffix(".git")) if url.strip() else None
    if existing is not None and existing.is_dir():
        st.caption(f"`{existing.name}` already exists locally and will be removed and re-fetched.")

    if not st.button("Fetch repository", disabled=not url.strip(), key="repo_git_fetch"):
        return None

    with st.spinner("Downloading repository…"):
        ok, result = fetch_repo(url, ref, token, project_root)

    if not ok:
        st.error(result)
        return None

    st.caption(f"Fetched into `Sample_Repos/{result}`")
    return result


def render_repo_source(project_root: Path, detect_repos) -> str | None:
    """Render the repository source chooser.

    Returns the name of a repo acquired on this run, or None. The active
    selection always lives in st.session_state.selected_repo.
    """
    st.subheader("Repository")
    mode = st.radio(
        "Source",
        _MODES,
        key="_repo_source_mode",
        label_visibility="collapsed",
    )

    acquired = None
    if mode == "Upload .zip":
        acquired = _render_upload(project_root)
    elif mode == "Git URL":
        acquired = _render_git_url(project_root)

    # Must be written before the selectbox below instantiates the same key.
    if acquired:
        st.session_state.selected_repo = acquired
        st.session_state.just_uploaded_repo = True

    repos = detect_repos(project_root)
    if not repos:
        st.caption("No repositories found yet — upload a .zip or fetch one by URL.")
        st.text_input("Repository name", key="selected_repo")
        return acquired

    # Seed the key instead of passing index=; supplying both a default and a
    # session-state-managed key makes Streamlit log a duplication warning.
    if st.session_state.get("selected_repo") not in repos:
        st.session_state.selected_repo = repos[0]

    st.selectbox(
        "Active repository",
        repos,
        key="selected_repo",
        help="The repository to analyse or query.",
    )
    return acquired
