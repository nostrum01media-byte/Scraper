import os
import shutil
import tempfile
from urllib.parse import urljoin, urlparse

import requests
import streamlit as st
from bs4 import BeautifulSoup


def is_media_url(url: str) -> bool:
    """Check if a URL ends with a common image or video extension."""
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    return ext in {
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
        ".mp4", ".webm", ".ogg", ".mov", ".avi", ".mkv"
    }


def collect_media_links(page_url: str) -> list[str]:
    """Fetch the page and return absolute URLs of all media files."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; MediaScraper/1.0; "
            "+https://github.com/nostrum01media-byte/Scraper)"
        )
    }
    resp = requests.get(page_url, timeout=15, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    media_urls = set()

    # Images
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            media_urls.add(urljoin(page_url, src))

    # Videos and <source> tags inside <video>
    for video in soup.find_all("video"):
        src = video.get("src")
        if src:
            media_urls.add(urljoin(page_url, src))
        for source in video.find_all("source"):
            src = source.get("src")
            if src:
                media_urls.add(urljoin(page_url, src))

    # Keep only known media extensions
    return [u for u in media_urls if is_media_url(u)]


def download_media(urls: list[str], out_dir: str) -> list[str]:
    """Download each URL into `out_dir`; return list of saved file paths."""
    saved_files = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; MediaScraper/1.0; "
            "+https://github.com/nostrum01media-byte/Scraper)"
        )
    }
    for url in urls:
        try:
            st.write(f"Attempting to download: {url}")
            r = requests.get(url, stream=True, timeout=15, headers=headers)
            r.raise_for_status()
            filename = os.path.basename(url.split("?")[0])
            if not filename:
                filename = "file_" + os.urandom(4).hex()
            path = os.path.join(out_dir, filename)
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            saved_files.append(path)
            st.success(f"Downloaded {filename}")
        except Exception as e:
            st.error(f"❌ Failed to download {url}: {e}")
    return saved_files


# ------------------------------------------------------------
# Streamlit UI
# ------------------------------------------------------------
st.set_page_config(page_title="Media Scraper", layout="centered")
st.title("🔎 Media Scraper")
st.caption("Enter a web page URL and download all images & videos found on that page.")

page_url = st.text_input("Page URL", placeholder="https://example.com")

if st.button("Scrape"):
    if not page_url:
        st.error("Please provide a URL.")
    else:
        with st.spinner("Fetching page and locating media…"):
            try:
                st.info("Fetching the page...")
                media_links = collect_media_links(page_url)
                st.info(f"Found {len(media_links)} media links.")
                if not media_links:
                    st.info("No image or video links were detected on this page.")
                else:
                    with st.expander("Show raw media URLs"):
                        for u in media_links:
                            st.write(u)

                    tmp_dir = tempfile.mkdtemp()
                    st.info("Downloading media files...")
                    downloaded = download_media(media_links, tmp_dir)

                    if downloaded:
                        # Create ZIP archive
                        zip_path = os.path.join(tmp_dir, "media.zip")
                        shutil.make_archive(base_name=zip_path[:-4], format="zip", root_dir=tmp_dir)

                        with open(zip_path, "rb") as f:
                            st.download_button(
                                label="📦 Download all media as ZIP",
                                data=f,
                                file_name="media.zip",
                                mime="application/zip",
                            )

                        st.subheader("Preview & Individual Downloads")
                        for file_path, url in zip(downloaded, media_links):
                            name = os.path.basename(file_path)
                            if name.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
                                st.image(file_path, caption=name, width=300)
                                with open(file_path, "rb") as img_f:
                                    st.download_button(
                                        label=f"Download {name}",
                                        data=img_f,
                                        file_name=name,
                                        mime="image/*",
                                        key=f"img_{name}",
                                    )
                            elif name.lower().endswith(
                                (".mp4", ".webm", ".ogg", ".mov", ".avi", ".mkv")
                            ):
                                st.video(file_path, format="video/mp4")
                                with open(file_path, "rb") as vid_f:
                                    st.download_button(
                                        label=f"Download {name}",
                                        data=vid_f,
                                        file_name=name,
                                        mime="video/*",
                                        key=f"vid_{name}",
                                    )
                            st.caption(f"Source: {url}")
                    else:
                        st.info("No downloadable media could be saved.")
            except requests.exceptions.RequestException as exc:
                st.error(f"❗ Network error: {exc}")
            except Exception as exc:
                st.error(f"❗ An error occurred: {exc}")
