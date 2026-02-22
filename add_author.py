import sqlite3

DB_PATH = "books.db"

# Manual author updates for this batch
manual_authors = {
    "oliver_twist": "Charles Dickens",
    "paradise_lost": "John Milton",
    "peter_pan": "J. M. Barrie",
    "pride_and_prejudice": "Jane Austen",
    "principles_of_political_economy_vol_1": "Wilhelm Roscher",
    "rambles_of_an_archaeologist": "Frederick William Fairholt",
    "right_ho_jeeves": "P. G. Wodehouse",
    "romeo_and_juliet": "William Shakespeare",
    "second_treatise_of_government": "John Locke",
    "sense_and_sensibility_161": "Jane Austen",
    "simple_sabotage_field_manual": "United States Office of Strategic Services",
    "adventures_of_ferdinand_count_fathom": "Tobias Smollett",
    "adventures_of_roderick_random": "Tobias Smollett",
    "adventures_of_sherlock_holmes": "Arthur Conan Doyle",
    "adventures_of_tom_sawyer_complete": "Mark Twain",
    "the_aeneid": "Virgil",
    "the_blue_castle": "L. M. Montgomery",
    "the_book_of_christmas": "Various",
    "the_brothers_karamazov": "Fyodor Dostoyevsky",
    "the_complete_works_of_william_shakespeare": "William Shakespeare",
    "the_confessions_of_st_augustine": "Saint Augustine of Hippo",
    "the_count_of_monte_cristo": "Alexandre Dumas and Auguste Maquet",
    "the_divine_comedy": "Dante Alighieri",
    "the_enchanted_april": "Elizabeth Von Arnim",
    "the_expedition_of_humphry_clinker": "Tobias Smollett",
    "the_great_gatsby": "F. Scott Fitzgerald",
    "the_history_of_human_marriage": "Edward Westermarck",
    "the_hound_of_the_baskervilles": "Arthur Conan Doyle",
    "the_iliad": "Homer",
    "the_importance_of_being_earnest": "Oscar Wilde",
    "the_jewish_state": "Theodor Herzl",
    "the_kama_sutra_of_vatsyayana": "Vatsyayana",
    "the_king_in_yellow": "Robert W. Chambers",
    "the_lesser_key_of_solomon_goetia": "Unknown",
    "the_odyssey": "Homer",
    "the_philosophy_of_auguste_comte": "Lucien Lévy-Bruhl",
    "the_picture_of_dorian_gray": "Oscar Wilde",
    "the_prince": "Niccolò Machiavelli",
    "the_republic": "Plato",
    "the_roll_of_honour_vol_1": "Melville Henry Massue Ruvigny et Raineval",
    "the_romance_of_lust": "Anonymous",
    "the_scarlet_letter": "Nathaniel Hawthorne",
    "the_souls_of_black_folk": "W. E. B. Du Bois",
    "the_strange_case_of_dr_jekyll_and_mr_hyde": "Robert Louis Stevenson",
    "the_travels_of_marco_polo_vol_1": "Marco Polo and Rusticiano da Pisa",
    "the_wonderful_wizard_of_oz": "L. Frank Baum",
    "the_works_of_edgar_allan_poe_vol_2": "Edgar Allan Poe",
    "the_yellow_wallpaper": "Charlotte Perkins Gilman",
    "thus_spake_zarathustra": "Friedrich Wilhelm Nietzsche",
    "treasure_island": "Robert Louis Stevenson",
    "twenty_years_after": "Alexandre Dumas and Auguste Maquet",
    "ulysses": "James Joyce",
    "walden_and_on_the_duty_of_civil_disobedience": "Henry David Thoreau",
    "war_and_peace": "Leo Tolstoy",
    "white_nights_and_other_stories": "Fyodor Dostoyevsky",
    "wuthering_heights": "Emily Brontë",
    "chikeokuotan": "Shizhen Wang",
    "kan": "Jun'ichiro Tanizaki"
}

# Connect to the SQLite database
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

for book_id, author in manual_authors.items():
    c.execute(
        "UPDATE books SET author = ? WHERE book_id = ?",
        (author, book_id)
    )
    print(f"Updated {book_id} → {author}")

conn.commit()
conn.close()

print("\nManual author update complete.")
