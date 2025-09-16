#!/usr/bin/env python3
"""
media_scraper_app.py – a Streamlit web app that downloads all images
and videos from a user‑provided URL.
"""

import os
import shutil
import tempfile
from urllib.parse import urljoin, urlparse

import requests
import streamlit as st
from bs4 import BeautifulSoup

# ------------------------------------------------------------
# Helper functions (same logic as the original script)
# ------------------------------------------------------------
def is_media_url(url: str) -> bool:
    """True if the URL ends with a common image/video extension."""
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    return ext in {
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
        ".mp4", ".webm", ".ogg", ".mov", ".avi", ".mkv"
    }

def collect_media_links(page_url: str) -> list[str]:
    """Fetch the page and return absolute URLs of all media files."""
    resp = requests.get(page_url, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    media_urls = set()

    # <img src=...>
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            media_urls.add(urljoin(page_url, src))

    # <video src=...> and <video><source src=...></source></video>
    for video in soup.find_all("video"):
        src = video.get("src")
        if src:
            media_urls.add(urljoin(page_url, src))
        for source in video.find_all("source"):
            src = source.get("src")
            if src:
                media_urls.add(urljoin(page_url, src))

    # Filter only known media extensions
    return [u for u in media_urls if is_media_url(u)]

def download_media(urls: list[str], out_dir: str) -> list[str]:
    """Download each URL into `out_dir`; return list of saved file paths."""
    saved_files = []
    for url in urls:
        try:
            r = requests.get(url, stream=True, timeout=15)
            r.raise_for_status()
            filename = os.path.basename(url.split("?")[0])
            # Guard against empty names
            if not filename:
                filename = "file_" + os.urandom(4).hex()
            path = os.path.join(out_dir, filename)
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            saved_files.append(path)
        except Exception as e:
            st.warning(f"❌ Failed to download {url}: {e}")
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
                media_links = collect_media_links(page_url)
                if not media_links:
                    st.info("No image or video links were detected on this page.")
                else:
                    st.success(f"Found **{len(media_links)}** media files.")
                    # Use a temporary directory so we don’t clutter the host
                    tmp_dir = tempfile.mkdtemp()
                    downloaded = download_media(media_links, tmp_dir)

                    # Show a download‑zip button
                    if downloaded:
                        zip_path = os.path.join(tmp_dir, "media.zip")
                        shutil.make_archive(base_name=zip_path[:-4], format="zip", root_dir=tmp_dir)

                        with open(zip_path, "rb") as f:
                            st.download_button(
                                label="📦 Download all media as ZIP",
                                data=f,
                                file_name="media.zip",
                                mime="application/zip",
                            )
                        # Also list a few files as preview
                        st.subheader("Sample files")
                        for file_path in downloaded[:5]:
                            name = os.path.basename(file_path)
                            if name.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
                                st.image(file_path, caption=name, width=200)
                            elif name.lower().endswith((".mp4", ".webm", ".ogg", ".mov", ".avi", ".mkv")):
                                st.video(file_path, format="video/mp4")
                    else:
                        st.info("No downloadable media could be saved.")
            except Exception as exc:
                st.error(f"❗ An error occurred: {exc}")
