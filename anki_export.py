#!/usr/bin/env python3

import genanki
from utils import MODEL_ID, DECK_ID_BASE


def detect_curriculum_pattern(collection_name, decks_info):
    """
    Detect if this is a curriculum-style collection (e.g., "RIME 1.1.3")
    Returns: (is_curriculum, base_name, block_num, unit_num, week_num)
    """
    import re

    # Pattern to match curriculum naming like "RIME 1.1.3", "FOUNDATIONS 2.3.1", etc.
    curriculum_pattern = r"^([A-Z][A-Z\s]+)\s+(\d+)\.(\d+)\.(\d+)$"
    match = re.match(curriculum_pattern, collection_name.strip().upper())

    if match:
        base_name = match.group(1).strip()
        block_num = match.group(2)
        unit_num = match.group(3)
        week_num = match.group(4)
        return True, base_name, block_num, unit_num, week_num

    return False, None, None, None, None


def export_hierarchical_apkg(
    data, collection_name, decks_info, path, is_single_deck=False
):
    """
    Export cards with hierarchical deck structure:

    For single deck URLs:
    Deck Name
    ├── Patient 1
    ├── Patient 2
    └── Patient 3

    For curriculum collections (e.g., RIME 1.1.3):
    Base Name (e.g., RIME)
    └── Block X
        └── Unit Y
            └── Week Z
                ├── Patient 1
                ├── Patient 2
                └── Patient 3

    For regular collections:
    Collection Name
    ├── Deck 1
    │   ├── Patient 1
    │   ├── Patient 2
    │   └── Patient 3
    └── Deck 2
        ├── Patient 1
        └── Patient 2
    """
    mcq_model = genanki.Model(
        MODEL_ID,
        "MCQ Q&A",
        fields=[
            {"name": "Front"},
            {"name": "CorrectAnswer"},
            {"name": "Explanation"},
            {"name": "ScoreText"},
            {"name": "Percent"},
            {"name": "Sources"},
            {"name": "Multi"},
            {"name": "CardId"},
        ],
        css="""
.background { margin-bottom: 16px; }
.question    { font-size: 1.1em; margin-bottom: 8px; font-weight: bold; }
.options     { border: 1px solid #666; padding: 10px; display: inline-block; }
.option      { margin: 6px 0; }
.option input{ margin-right: 6px; }
#answer-section { margin-top: 12px; }
.correct { color: green !important; font-weight: bold; }
.incorrect { color: red !important; }
hr#answer-divider { border: none; border-top: 1px solid #888; margin: 16px 0; }
#answer-section { color: white; }
#explanation { color: white; }

/* Support for full card content rendering */
.full-card-content { 
    margin-bottom: 20px; 
    border: 1px solid #ccc; 
    padding: 15px; 
    background: #f9f9f9; 
    border-radius: 5px;
}

.full-card-content .container.card {
    background: white;
    border: none;
    padding: 0;
}

/* Vital signs monitor styling */
.vital-signs-monitor {
    background: #1a1a1a;
    color: #00ff00;
    font-family: 'Courier New', monospace;
    padding: 15px;
    border: 2px solid #333;
    border-radius: 8px;
    margin: 10px 0;
}

.monitor {
    background: #000;
    color: #00ff00;
    font-family: monospace;
    padding: 10px;
    border: 1px solid #333;
}

/* Table styling improvements */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
    background: white;
    color: black;
}

table th, table td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
    color: black !important;
    background: white;
}

table th {
    background-color: #f2f2f2 !important;
    font-weight: bold;
    color: black !important;
}

/* Specific styling for tables in explanation/answer sections */
#explanation table, #answer-section table {
    background: white !important;
    color: black !important;
    border: 2px solid #333;
    margin: 15px 0;
}

#explanation table th, #answer-section table th {
    background-color: #e6e6e6 !important;
    color: black !important;
    font-weight: bold;
    border: 1px solid #666;
}

#explanation table td, #answer-section table td {
    background: white !important;
    color: black !important;
    border: 1px solid #666;
}

/* Style medical table headers */
#explanation h4, #answer-section h4 {
    color: #4CAF50;
    font-weight: bold;
    margin-top: 20px;
    margin-bottom: 10px;
}

/* Styling for extracted images */
.extracted-images {
    margin: 15px 0;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    background: #fafafa;
}

.extracted-images img {
    max-width: 100%;
    height: auto;
    margin: 5px;
    border: 1px solid #ccc;
    border-radius: 3px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Responsive image sizing */
.extracted-images img[width] {
    max-width: 100% !important;
    width: auto !important;
    height: auto !important;
}
""",
        templates=[
            {
                "name": "Card 1",
                "qfmt": """
{{Front}}
<script>
(function(){
  var cid = "{{CardId}}", key = "sel_"+cid;
  // Reset stored selections each time the card front loads
  localStorage.removeItem(key);
  var saved = JSON.parse(localStorage.getItem(key) || '[]');
  saved.forEach(function(id){
    var inp = document.getElementById(id);
    if(inp) inp.checked = true;
  });
  document.querySelectorAll('.option input').forEach(function(inp){
    inp.addEventListener('change', function(){
      var sel = Array.from(
        document.querySelectorAll('.option input:checked')
      ).map(function(e){ return e.id; });
      localStorage.setItem(key, JSON.stringify(sel));
    });
  });
})();
</script>
""",
                "afmt": """
{{Front}}
<script>
(function(){
  var cid = "{{CardId}}", key = "sel_"+cid,
      saved = JSON.parse(localStorage.getItem(key) || '[]');
  saved.forEach(function(id){
    var inp = document.getElementById(id);
    if(inp) inp.checked = true;
  });
})();
</script>
<hr id="answer-divider">
<script>
(function(){
  var answers = "{{CorrectAnswer}}".split(" ||| ").map(function(s){ return s.trim(); });
  document.querySelectorAll('.option label').forEach(function(lbl){
    var text = lbl.innerText.trim(),
        inp  = document.getElementById(lbl.getAttribute('for'));
    if(answers.includes(text)){
      lbl.classList.add('correct');
    } else if(inp && inp.checked){
      lbl.classList.add('incorrect');
    }
  });
})();
</script>
<div id="answer-section">
  <b>Correct answer(s):</b> {{CorrectAnswer}}<br>
  <b>Score:</b> <span id="score-text">{{ScoreText}}</span><br>
  <b>Percent:</b> <span id="percent-text">{{Percent}}</span>
</div>
<script>
(function(){
  var answers = "{{CorrectAnswer}}".split(" ||| ").map(function(s){ return s.trim(); });
  var selected = Array.from(document.querySelectorAll('.option input:checked')).map(function(inp){ return inp.value.trim(); });
  var correctLen = answers.length;
  var selectedCorrect = 0;
  
  // More robust text comparison - normalize both sides
  selected.forEach(function(val){
    // Check if this selected value matches any of the correct answers
    var normalizedVal = val.replace(/\\s+/g, ' ').trim();
    var isCorrect = answers.some(function(answer){
      var normalizedAnswer = answer.replace(/\\s+/g, ' ').trim();
      return normalizedVal === normalizedAnswer;
    });
    if(isCorrect) selectedCorrect++;
  });
  
  var scoreEl = document.getElementById('score-text');
  var pctEl = document.getElementById('percent-text');
  if(scoreEl){
    scoreEl.innerText = selectedCorrect + " / " + correctLen;
  }
  if(pctEl){
    var pct = correctLen > 0 ? Math.round((selectedCorrect / correctLen) * 100) : 0;
    pctEl.innerText = pct + "%";
  }
})();
</script>
{{#Sources}}
<hr>
<div id="sources">
  <b>Sources:</b><br>
  {{{Sources}}}
</div>
{{/Sources}}
<hr>
{{#Explanation}}
<div id="explanation"><b>Explanation:</b> {{Explanation}}</div>
{{/Explanation}}
""",
            }
        ],
    )

    text_model = genanki.Model(
        MODEL_ID + 1,
        "FreeText Q&A",
        fields=[{"name": "Front"}, {"name": "CorrectAnswer"}, {"name": "Explanation"}],
        css=mcq_model.css,
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": """
{{Front}}
<hr id="answer-divider">
<div id="answer-section">
  <b>Answer:</b> <span style="color:white;">{{CorrectAnswer}}</span>
</div>
{{#Explanation}}
<div id="explanation"><b>Explanation:</b> <span style="color:white;">{{Explanation}}</span></div>
{{/Explanation}}
""",
            }
        ],
    )

    # Check if this is a curriculum-style collection
    is_curriculum, base_name, block_num, unit_num, week_num = detect_curriculum_pattern(
        collection_name, decks_info
    )

    # Group cards by deck and patient
    deck_structure = {}

    for card in data:
        deck_title = card.get("deck_title", "Unknown Deck")
        patient_info = card.get("patient_info", "Unknown Patient")

        # Check if this is a sequential card (no patient organization)
        is_sequential = card.get("is_sequential", False)

        if deck_title not in deck_structure:
            deck_structure[deck_title] = {}

        # For sequential cards, group directly under deck without patient subdivision
        if is_sequential:
            patient_key = "__sequential__"  # Special key for sequential cards
        else:
            patient_key = patient_info

        if patient_key not in deck_structure[deck_title]:
            deck_structure[deck_title][patient_key] = []

        deck_structure[deck_title][patient_key].append(card)

    # Create hierarchical decks
    decks = []
    deck_id_counter = DECK_ID_BASE

    if is_single_deck:
        # For single deck URLs, create simple Deck::Patient hierarchy
        actual_deck_name = collection_name
        if (
            data
            and data[0].get("deck_title")
            and data[0]["deck_title"] != "Unknown Deck"
        ):
            actual_deck_name = data[0]["deck_title"]

        # Group by patient only (no deck grouping needed for single deck)
        patient_structure = {}
        has_sequential_cards = False

        for card in data:
            patient_info = card.get("patient_info", "Unknown Patient")
            is_sequential = card.get("is_sequential", False)

            if is_sequential:
                has_sequential_cards = True
                patient_key = "__sequential__"
            else:
                patient_key = patient_info

            if patient_key not in patient_structure:
                patient_structure[patient_key] = []
            patient_structure[patient_key].append(card)

        # Handle sequential cards differently - no patient subdivision
        if has_sequential_cards and "__sequential__" in patient_structure:
            # For sequential decks, create a single deck with all cards directly under it
            hierarchical_name = f"{actual_deck_name} (Sequential Deck)"

            deck = genanki.Deck(deck_id_counter, hierarchical_name)
            deck_id_counter += 1

            sequential_cards = patient_structure["__sequential__"]

            for i, card in enumerate(sequential_cards):
                # Create Anki note from card data
                _add_card_to_deck(
                    deck,
                    card,
                    i,
                    actual_deck_name,
                    mcq_model,
                    text_model,
                    is_sequential=True,
                )

            decks.append(deck)

        # Handle regular patient-organized cards
        for patient_info, cards in patient_structure.items():
            if patient_info == "__sequential__":
                continue  # Already handled above

            # Create simple hierarchy: "DeckName::Patient"
            hierarchical_name = f"{actual_deck_name}::{patient_info}"

            deck = genanki.Deck(deck_id_counter, hierarchical_name)
            deck_id_counter += 1

            for i, card in enumerate(cards):
                _add_card_to_deck(
                    deck, card, i, actual_deck_name, mcq_model, text_model, patient_info
                )

            decks.append(deck)

    elif is_curriculum:
        # For curriculum collections, create Base::Block::Unit::Week::Deck::Patient hierarchy
        for deck_title, patients in deck_structure.items():
            for patient_info, cards in patients.items():
                if patient_info == "__sequential__":
                    # Curriculum sequential deck
                    hierarchical_name = f"{base_name}::Block {block_num}::Unit {unit_num}::Week {week_num}::{deck_title} (Sequential)"
                else:
                    # Regular curriculum deck
                    hierarchical_name = f"{base_name}::Block {block_num}::Unit {unit_num}::Week {week_num}::{deck_title}::{patient_info}"

                deck = genanki.Deck(deck_id_counter, hierarchical_name)
                deck_id_counter += 1

                for i, card in enumerate(cards):
                    _add_card_to_deck(
                        deck,
                        card,
                        i,
                        deck_title,
                        mcq_model,
                        text_model,
                        patient_info,
                        curriculum_info=(base_name, block_num, unit_num, week_num),
                    )

                decks.append(deck)
    else:
        # For regular collections, use the existing Collection::Deck::Patient hierarchy
        for deck_title, patients in deck_structure.items():
            for patient_info, cards in patients.items():
                if patient_info == "__sequential__":
                    # Sequential deck in collection
                    hierarchical_name = f"{collection_name}::{deck_title} (Sequential)"
                else:
                    # Regular collection deck
                    hierarchical_name = (
                        f"{collection_name}::{deck_title}::{patient_info}"
                    )

                deck = genanki.Deck(deck_id_counter, hierarchical_name)
                deck_id_counter += 1

                for i, card in enumerate(cards):
                    _add_card_to_deck(
                        deck,
                        card,
                        i,
                        deck_title,
                        mcq_model,
                        text_model,
                        patient_info,
                        collection_name=collection_name,
                    )

                decks.append(deck)

    # Create package with all decks
    package = genanki.Package(decks)
    package.write_to_file(path)

    print(f"✅ Created Anki deck: {path}")
    print(f"📊 Generated {len(decks)} sub-decks with hierarchical structure")


def _add_card_to_deck(
    deck,
    card,
    index,
    deck_title,
    mcq_model,
    text_model,
    patient_info=None,
    is_sequential=False,
    curriculum_info=None,
    collection_name=None,
):
    """Helper function to add a card to a deck with proper formatting"""
    multi_flag = card.get("multi", False)
    multi = "1" if multi_flag else ""
    sources_html = "".join(f"<li>{src}</li>" for src in card.get("sources", []))
    model = text_model if card.get("freetext") else mcq_model

    if card.get("freetext"):
        fields = [
            card["question"],
            card["answer"],
            card.get("explanation", ""),
        ]
    else:
        fields = [
            card["question"],
            card["answer"],
            card.get("explanation", ""),
            card.get("score_text", ""),
            card.get("percent", ""),
            sources_html,
            multi,
            card["id"],
        ]

    # Build comprehensive tags
    tags = card.get("tags", [])

    if curriculum_info:
        base_name, block_num, unit_num, week_num = curriculum_info
        tags.extend(
            [
                f"Curriculum_{base_name.replace(' ', '_')}",
                f"Block_{block_num}",
                f"Unit_{unit_num}",
                f"Week_{week_num}",
            ]
        )

    if collection_name:
        tags.append(f"Collection_{collection_name.replace(' ', '_')}")

    tags.append(f"Deck_{deck_title.replace(' ', '_')}")

    if is_sequential:
        tags.extend(["Sequential_Mode", f"Question_{index+1}"])
    elif patient_info:
        tags.append(f"Patient_{patient_info.replace(' ', '_')}")

    deck.add_note(
        genanki.Note(
            model=model,
            fields=fields,
            tags=tags,
        )
    )


def export_apkg(data, deck_name, path):
    """Simple APKG export for backwards compatibility"""
    mcq_model = genanki.Model(
        MODEL_ID,
        "MCQ Q&A",
        fields=[
            {"name": "Front"},
            {"name": "CorrectAnswer"},
            {"name": "Explanation"},
            {"name": "ScoreText"},
            {"name": "Percent"},
            {"name": "Sources"},
            {"name": "Multi"},
            {"name": "CardId"},
        ],
        css="""
.background { margin-bottom: 16px; }
.question    { font-size: 1.1em; margin-bottom: 8px; font-weight: bold; }
.options     { border: 1px solid #666; padding: 10px; display: inline-block; }
.option      { margin: 6px 0; }
.option input{ margin-right: 6px; }
#answer-section { margin-top: 12px; }
.correct { color: green !important; font-weight: bold; }
.incorrect { color: red !important; }
hr#answer-divider { border: none; border-top: 1px solid #888; margin: 16px 0; }
#answer-section { color: white; }
#explanation { color: white; }
""",
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": """
{{Front}}
<hr id="answer-divider">
<div id="answer-section">
  <b>Correct answer(s):</b> {{CorrectAnswer}}<br>
  <b>Score:</b> {{ScoreText}}<br>
  <b>Percent:</b> {{Percent}}
</div>
{{#Explanation}}
<div id="explanation"><b>Explanation:</b> {{Explanation}}</div>
{{/Explanation}}
""",
            }
        ],
    )

    deck = genanki.Deck(DECK_ID_BASE, deck_name)

    for card in data:
        multi_flag = card.get("multi", False)
        multi = "1" if multi_flag else ""
        sources_html = "".join(f"<li>{src}</li>" for src in card.get("sources", []))

        fields = [
            card["question"],
            card["answer"],
            card.get("explanation", ""),
            card.get("score_text", ""),
            card.get("percent", ""),
            sources_html,
            multi,
            card["id"],
        ]

        deck.add_note(
            genanki.Note(
                model=mcq_model,
                fields=fields,
                tags=card.get("tags", []),
            )
        )

    package = genanki.Package([deck])
    package.write_to_file(path)
    print(f"✅ Created Anki deck: {path}")
