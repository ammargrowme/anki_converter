#!/usr/bin/env python3
"""
export_ucalgary_anki.py

Convert UCalgary Cards flashcards into Anki decks.
Supports:
  - Automatic: scan all collections → all decks → all cards
  - Manual collection: one collection → all decks → cards
  - Manual deck: one deck → cards

Outputs:
  - <out-prefix>.json   (raw data)
  - <out-prefix>.csv    (tab-delimited for Anki import)
  - <out-prefix>.apkg   (Anki package with media)
"""

import os
import re
import csv
import argparse
import requests
from bs4 import BeautifulSoup
import genanki
from dotenv import load_dotenv

# ─── Load .env (if present) ─────────────────────────────────────────────────
# Reads UC_EMAIL and UC_PW from a .env file in the working directory, if it exists.
load_dotenv()

# ─── Configuration ─────────────────────────────────────────────────────────────
BASE_URL = "https://cards.ucalgary.ca"
LOGIN_URL = f"{BASE_URL}/login"

# Unique IDs for genanki — adjust if you re-run to avoid collisions
DECK_ID_BASE = 1607392319000
MODEL_ID = 1607392319001


# ─── Authentication ────────────────────────────────────────────────────────────
def login(session, email, password):
    """Authenticate against cards.ucalgary.ca and persist cookies in session."""
    # Fetch login page to get CSRF token (if any)
    r = session.get(LOGIN_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    token_input = soup.find("input", {"name": "csrf_token"})
    token = token_input["value"] if token_input else None

    payload = {"email": email, "password": password}
    if token:
        payload["csrf_token"] = token

    r2 = session.post(LOGIN_URL, data=payload)
    r2.raise_for_status()
    if "Logout" not in r2.text:
        raise RuntimeError(
            "Login failed – please check your UC_EMAIL/UC_PW or credentials."
        )


# ─── Fetch / Parse Helpers ────────────────────────────────────────────────────
def fetch(url, session):
    r = session.get(url)
    r.raise_for_status()
    return r.text


def fetch_json(url, session):
    r = session.get(url)
    r.raise_for_status()
    return r.json()


def parse_homepage(html):
    """Return list of all collections as dicts: [{'id','name'}]."""
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for div in soup.select("div.bag[rel]"):
        cid = div["rel"]
        name_elem = div.select_one("h3.bag-name")
        name = name_elem.get_text(strip=True) if name_elem else f"Collection {cid}"
        out.append({"id": cid, "name": name})
    return out


def parse_collection(html):
    """Return list of decks in a collection: [{'id','name'}]."""
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for a in soup.select("a.deck-name"):
        href = a["href"]
        m = re.match(r"/deck/(\d+)", href)
        if not m:
            continue
        out.append({"id": m.group(1), "name": a.get_text(strip=True)})
    return out


def parse_deck(html):
    """Return list of card IDs in a deck-details page."""
    soup = BeautifulSoup(html, "html.parser")
    return [div["rel"] for div in soup.select("div.patient[rel]")]


# ─── Card / Media Fetching ────────────────────────────────────────────────────
def fetch_card_data(card_id, session):
    """Fetch one card’s data via the JSON API."""
    url = f"{BASE_URL}/api/card/{card_id}.json"
    data = fetch_json(url, session)
    return {
        "id": data["id"],
        "question": data["question"].strip(),
        "answer": data["answer"].strip(),
        "tags": data.get("tags", []),
        "images": data.get("images", []),
    }


def download_media(media_urls, session, media_dir="media"):
    """
    Download each URL into ./media/
    Return list of local filepaths.
    """
    os.makedirs(media_dir, exist_ok=True)
    local_files = []
    for url in media_urls:
        fname = os.path.basename(url)
        path = os.path.join(media_dir, fname)
        if not os.path.exists(path):
            r = session.get(url)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
        local_files.append(path)
    return local_files


# ─── Export Functions ─────────────────────────────────────────────────────────
def export_json(data, path):
    import json

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[+] JSON written to {path}")


def export_csv(data, path):
    """
    Write tab-delimited file with columns:
      Question, Answer, Tags
    Embeds <image src="filename"> tags where appropriate.
    """
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Question", "Answer", "Tags"])
        for c in data:
            q = c["question"]
            a = c["answer"]
            # embed images in front field
            for img in c.get("media_loc", []):
                fname = os.path.basename(img)
                q += f'\n<img src="{fname}">'
            tags = " ".join(c.get("tags", []))
            writer.writerow([q, a, tags])
    print(f"[+] CSV written to {path}")


def export_apkg(data, deck_name, path):
    """Generate .apkg with genanki, embedding all media files."""
    model = genanki.Model(
        MODEL_ID,
        "Basic Q&A",
        fields=[{"name": "Question"}, {"name": "Answer"}],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Question}}",
                "afmt": "{{FrontSide}}<hr id=answer>{{Answer}}",
            }
        ],
    )
    deck = genanki.Deck(DECK_ID_BASE, deck_name)
    media_files = []
    for c in data:
        media_files.extend(c.get("media_loc", []))
        note = genanki.Note(
            model=model, fields=[c["question"], c["answer"]], tags=c.get("tags", [])
        )
        deck.add_note(note)

    pkg = genanki.Package(deck)
    # genanki expects basenames in media_files
    pkg.media_files = [mf for mf in media_files]
    pkg.write_to_file(path)
    print(f"[+] APKG written to {path}")


# ─── Gathering Workflows ──────────────────────────────────────────────────────
def gather_cards_from_deck(deck_id, session):
    html = fetch(f"{BASE_URL}/details/{deck_id}?bag_id={deck_id}", session)
    card_ids = parse_deck(html)
    cards = []
    for cid in card_ids:
        cd = fetch_card_data(cid, session)
        cd["media_loc"] = download_media(cd["images"], session)
        cards.append(cd)
    return cards


def gather_cards_from_collection(collection_id, session):
    html = fetch(f"{BASE_URL}/collection/{collection_id}", session)
    decks = parse_collection(html)
    all_cards = []
    for deck in decks:
        print(f"--> Deck {deck['id']}: {deck['name']}")
        cards = gather_cards_from_deck(deck["id"], session)
        # tag each card with its deck name
        for c in cards:
            c["tags"].append(deck["name"].replace(" ", "_"))
        all_cards.extend(cards)
    return all_cards


def gather_cards_auto(session):
    html = fetch(f"{BASE_URL}/collection", session)
    collections = parse_homepage(html)
    all_cards = []
    for coll in collections:
        print(f"== Collection {coll['id']}: {coll['name']}")
        cards = gather_cards_from_collection(coll["id"], session)
        # tag with collection name
        for c in cards:
            c["tags"].append(coll["name"].replace(" ", "_"))
        all_cards.extend(cards)
    return all_cards


# ─── Main CLI Entrypoint ─────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="Export UCalgary Cards → Anki")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--auto", action="store_true", help="Process all collections → decks → cards"
    )
    group.add_argument(
        "--collection",
        metavar="ID",
        help="Process one collection ID → all decks → cards",
    )
    group.add_argument("--deck", metavar="ID", help="Process one deck ID → cards only")

    p.add_argument("--username", help="UCalgary email (overrides .env UC_EMAIL)")
    p.add_argument("--password", help="UCalgary password (overrides .env UC_PW)")
    p.add_argument(
        "--out-prefix",
        default="output",
        help="Prefix for output files (default: 'output')",
    )

    args = p.parse_args()

    # Credentials: CLI flags take precedence over .env
    email = args.username or os.getenv("UC_EMAIL")
    pw = args.password or os.getenv("UC_PW")
    if not email or not pw:
        p.error(
            "Missing credentials: set UC_EMAIL and UC_PW in a .env file "
            "or pass --username/--password arguments."
        )

    session = requests.Session()
    login(session, email, pw)

    # Gather cards based on mode
    if args.auto:
        cards = gather_cards_auto(session)
        deck_name = "All_UCalgary_Collections"
    elif args.collection:
        cards = gather_cards_from_collection(args.collection, session)
        deck_name = f"Collection_{args.collection}"
    else:  # args.deck
        cards = gather_cards_from_deck(args.deck, session)
        deck_name = f"Deck_{args.deck}"

    # Exports
    out_json = f"{args.out_prefix}.json"
    out_csv = f"{args.out-prefix}.csv"
    out_apkg = f"{args.out_prefix}.apkg"

    export_json(cards, out_json)
    export_csv(cards, out_csv)
    export_apkg(cards, deck_name, out_apkg)


if __name__ == "__main__":
    main()
